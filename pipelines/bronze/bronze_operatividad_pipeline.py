from typing import Optional, Type, List, Dict

import pandas as pd

from common.session_manager import get_session
from config.app_config import AppConfig
from config.logging_pipeline import LoggingPipeline
from entities.bronze.bronze_operatividad_entity import BronzeOperatividadEntity
from etl.extract.db_extractor import DatabaseExtractor
from etl.load.db_load import DWBatchedLoader
from etl.transform.dtypes_massive import DtypeDateTransform, DtypeIntegerTransform, DtypeStringTransform
from etl.transform.general_functions import DropDuplicatesTransform, ConcatDataFrames, AddConstantColumn
from utils.RunMode import RunMode
from utils.general_functions import load_sql_statement
from utils.mode_persistence import ModePersistence
from utils.source_spec import SourceSpec


class DatabaseConfig:
    def __init__(self, app_config):
        self.db_alias_load: str = "LOCAL"
        self.model_class: Type[BronzeOperatividadEntity] = BronzeOperatividadEntity
        self.mode: ModePersistence = ModePersistence.UPDATE
        self.batch_size: int = 6000
        self.commit_per_batch: bool = True
        self.conflict_cols: tuple[str, ...] = ('id_tramite', 'origen', 'factura')
        self.update_cols: tuple[str, ...] = (
            'serial_firma', 'update_date', 'cedula', 'fecha_aprobacion', 'factura', 'ruc', 'tipo_firma', 'fecha_inicio_tramite',
            'ruc_aux',
            'medio', 'sf_control', 'producto', 'grupo_vendedor', 'estado', 'fecha_factura')


class PipelineConfig:
    def __init__(self, app_config):
        self.pipeline_name: str = "Bronze Operatividad Entity Pipeline"
        self.mode_pipeline: RunMode = app_config.run_mode
        self.COLUMNS_STRING = ['cedula', 'factura', 'ruc', 'tipo_firma', 'serial_firma', 'ruc_aux', 'medio', 'producto',
                               'estado']
        self.COLUMNS_INTEGER = ['sf_control']
        self.COLUMNS_DATETIME = ['fecha_aprobacion', 'fecha_inicio_tramite', 'fecha_factura']
        self.SOURCE_BY_MODE: Dict[RunMode, List[SourceSpec]] = {
            RunMode.INICIAL: [
                SourceSpec("Camunda", "CAMUNDA", "initialization", "camunda_productos.sql"),
                SourceSpec("Camunda", "CAMUNDA", "initialization", "camunda_productos_no_aprobados.sql"),
                SourceSpec("portales SD", "PORTAL", "initialization", "portales_productos.sql"),
                SourceSpec("portales GK", "PORTAL_GK", "initialization", "portales_gk_productos.sql")

            ],
            RunMode.INCREMENTAL: [
                SourceSpec("Camunda", "CAMUNDA", "incremental", "camunda_productos_incremental.sql"),
                SourceSpec("Camunda", "CAMUNDA", "incremental", "camunda_productos_no_aprobados_incremental.sql")
            ]
        }


class BronzeOperatividadPipeline:
    def __init__(
            self,
            app_config: AppConfig,
            database_config: Optional[DatabaseConfig] = None,
            pipeline_config: Optional[PipelineConfig] = None
    ) -> None:
        self.database_config = database_config or DatabaseConfig(app_config)
        self.pipeline_config = pipeline_config or PipelineConfig(app_config)

    def _build_params_for_mode(self, query_file) -> Optional[dict[str, object]]:
        if self.pipeline_config.mode_pipeline == RunMode.INICIAL:
            return None
        elif query_file == 'camunda_productos_incremental.sql':
            with get_session(self.database_config.db_alias_load) as session:
                where_func = lambda q: q.filter(
                    self.database_config.model_class.estado == "APROBADO"
                )
                max_incremental_date = self.database_config.model_class.get_last_approbation_date(session, where_func)
        elif query_file == 'camunda_productos_no_aprobados_incremental.sql':
            with get_session(self.database_config.db_alias_load) as session:
                where_func = lambda q: q.filter(
                    self.database_config.model_class.estado == "NO APROBADO"
                )
                max_incremental_date = self.database_config.model_class.get_last_billing_date(session, where_func)
        print(max_incremental_date)
        return {"max_incremental_date": max_incremental_date}

    def _build_pipeline(self, spec: SourceSpec, sql_text: str, params: Optional[Dict[str, object]]) -> LoggingPipeline:
        steps = [
            ("Extract Data from Portales and Camunda Database",
             DatabaseExtractor(db_alias=spec.db_alias_load, query=sql_text, params=params)),
            ("Transform Data Type DateTime", DtypeDateTransform(self.pipeline_config.COLUMNS_DATETIME)),
            ("Transform Data Type Integer", DtypeIntegerTransform(self.pipeline_config.COLUMNS_INTEGER)),
            ("Transform Data Type String", DtypeStringTransform(self.pipeline_config.COLUMNS_STRING)),
            ("Add Column Origin", AddConstantColumn("origen", spec.db_alias_load)),
        ]
        return LoggingPipeline(steps, pipeline_name=f"Pipeline Extract {spec.name.upper()}")

    def _integration_pipeline(self) -> LoggingPipeline:
        """
        Pipeline de integración/normalización común a todas las fuentes.
        """
        # Replaces declarativos generados dinámicamente

        steps = [
            ("Union de varios DF", ConcatDataFrames()),
            ("Eliminar duplicados por 'serial_firma'", DropDuplicatesTransform(["serial_firma"])),
            ("Eliminar duplicados por 'serial_firma'", DropDuplicatesTransform(['id_tramite', 'origen', 'factura'])),
            ("Load DatawareHouse Bronze Operatividad", DWBatchedLoader(
                db_alias=self.database_config.db_alias_load,
                model_class=self.database_config.model_class,
                mode=self.database_config.mode,
                batch_size=self.database_config.batch_size,
                commit_per_batch=self.database_config.commit_per_batch,
                update_cols=self.database_config.update_cols,
                conflict_cols=self.database_config.conflict_cols
            ))
        ]

        return LoggingPipeline(steps=steps, pipeline_name="Pipeline Integración y Normalización Tabla Operatividad")

    def run(self):
        """
        Ejecuta el pipeline de integración en modo INICIAL o INCREMENTAL.
        """

        frames: List[pd.DataFrame] = []

        # Construir y ejecutar un pipeline por Fuente
        for spec in self.pipeline_config.SOURCE_BY_MODE[self.pipeline_config.mode_pipeline]:
            params = self._build_params_for_mode(spec.query_file)
            query = load_sql_statement(spec.folder_name, spec.query_file)
            pipe = self._build_pipeline(spec, query, params)
            df = pipe.fit_transform(None)
            frames.append(df)
        self._integration_pipeline().fit_transform(frames)
