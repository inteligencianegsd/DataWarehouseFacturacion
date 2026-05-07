from dwh_facturacion.config.app_config import AppConfig
from dwh_facturacion.config.logging_pipeline import LoggingPipeline
from dwh_facturacion.entities.features.facturas_excluidas_entity import FeaturesFacturasExcluidasEntity

from typing import Optional, List, Dict, Type

from dwh_facturacion.etl.extract.db_extractor import DatabaseExtractor, CsvExtractor
from dwh_facturacion.etl.load.db_load import DWBatchedLoader
from dwh_facturacion.etl.transform.dtypes_massive import DtypeDateTransform
from dwh_facturacion.utils.RunMode import RunMode
from dwh_facturacion.utils.general_functions import load_sql_statement
from dwh_facturacion.utils.mode_persistence import ModePersistence
from dwh_facturacion.utils.mode_persistence import ModePersistence
from dwh_facturacion.utils.source_spec import SourceSpec
from pathlib import Path
from dwh_facturacion.utils.general_functions import load_csv_file



class DatabaseConfig:
    def __init__(self, app_config):
        self.db_alias_load: str = app_config.db_alias
        self.model_class: Type[FeaturesFacturasExcluidasEntity] = FeaturesFacturasExcluidasEntity
        self.mode: ModePersistence = ModePersistence.UPDATE
        self.conflict_cols: tuple[str, ...] = ('codigo_factura',)
        self.update_cols: tuple[str, ...] = ('update_date', 'motivo')
        self.commit_per_batch: bool = True


class PipelineConfig:
    def __init__(self, app_config):
        self.pipeline_name: str = "Features Facturas Exluidas Entity Pipeline"
        self.mode_pipeline: RunMode = app_config.run_mode

        self.SOURCE_BY_MODE: Dict[RunMode, List[SourceSpec]] = {
            RunMode.INICIAL: [
                SourceSpec("fenix", "FENIX", "initialization", "facturas_excluidas.sql")
            ],
            RunMode.INCREMENTAL: [
                SourceSpec("fenix", "FENIX", "incremental", "facturas_excluidas.sql")
            ]
        }
        self.CSV_PATH = load_csv_file("facturas_excluidas.csv")


class FeaturesFacturasExcluidasPipelines:
    def __init__(
            self,
            app_config: AppConfig,
            database_config: Optional[DatabaseConfig] = None,
            pipeline_config: Optional[PipelineConfig] = None
    ) -> None:
        self.database_config = database_config or DatabaseConfig(app_config)
        self.pipeline_config = pipeline_config or PipelineConfig(app_config)
        self.DATETIME_COLUMNS = ['creation_date', 'update_date']

    def _build_params_for_mode(self) -> Optional[dict[str, object]]:
        return None
        # Descomentar en caso de buscar una Act. incremental en funcion de un campo
        #     max_emission_date = DatabaseConfig.model_class.get_last_transaction_date(session)
        # return {"max_emission_date": max_emission_date}

    def _build_pipeline(self, spec: SourceSpec, sql_text: str, params: Optional[Dict[str, object]]) -> LoggingPipeline:
        is_initial = self.pipeline_config.mode_pipeline == RunMode.INICIAL

        # ── Extractor: CSV en INCREMENTAL, base de datos en INICIAL ──────────
        if is_initial:
            extractor = (
                "Extract Data from CSV (Incremental)",
                CsvExtractor(filepath=self.pipeline_config.CSV_PATH)
            )
        else:
            extractor = (
                "Extract Data from Fenix Database",
                DatabaseExtractor(db_alias=spec.db_alias_load, query=sql_text, params=params)
            )

        steps = [
            extractor,
            # ('Transformation DateTime Dtype', DtypeDateTransform(self.DATETIME_COLUMNS)),
            ("Load DatawareHouse Bronze Articulos", DWBatchedLoader(
                db_alias=self.database_config.db_alias_load,
                model_class=self.database_config.model_class,
                mode=self.database_config.mode,
                conflict_cols=self.database_config.conflict_cols,
                update_cols=self.database_config.update_cols,
                commit_per_batch=self.database_config.commit_per_batch,
            ))

        ]
        return LoggingPipeline(steps, pipeline_name=self.pipeline_config.pipeline_name)

    def run(self):
        """
        Ejecuta el pipeline de integración en modo INICIAL o INCREMENTAL.
        """
        params = self._build_params_for_mode()

        # Construir y ejecutar un pipeline por Fuente
        for spec in self.pipeline_config.SOURCE_BY_MODE[self.pipeline_config.mode_pipeline]:
            query = load_sql_statement(spec.folder_name, spec.query_file)
            pipe = self._build_pipeline(spec, query, params)
            pipe.fit_transform(None)
