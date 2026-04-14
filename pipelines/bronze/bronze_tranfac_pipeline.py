from typing import Optional, List, Dict, Type

from common.session_manager import get_session
from config.app_config import AppConfig
from config.logging_pipeline import LoggingPipeline
from entities.bronze.broze_tranfac_entity import BronzeTranfacEntity
from etl.extract.db_extractor import DatabaseExtractor
from etl.load.db_load import DWBatchedLoader
from utils.RunMode import RunMode
from utils.general_functions import load_sql_statement
from utils.mode_persistence import ModePersistence
from utils.source_spec import SourceSpec


class DatabaseConfig:

    def __init__(self, app_config):

        self.db_alias_load: str = app_config.db_alias
        self.model_class: Type[BronzeTranfacEntity] = BronzeTranfacEntity
        self.mode: ModePersistence = ModePersistence.UPDATE
        self.conflict_cols: tuple[str, ...] = ("id_tranfac", "unico")
        self.update_cols: tuple[str, ...] = ('numfac', 'codart', 'cantidad_d', 'precio', 'desct', 'iva')
        self.batch_size: int = 6000
        self.commit_per_batch: bool = True


class PipelineConfig:
    def __init__(self, app_config):
        self.pipeline_name: str = "Bronze Tranfac Entity Pipeline"
        self.mode_pipeline: RunMode = app_config.run_mode

        self.SOURCE_BY_MODE: Dict[RunMode, List[SourceSpec]] = {
            RunMode.INICIAL: [
                SourceSpec("fenix", "FENIX", "initialization", "tranfac.sql")
            ],
            RunMode.INCREMENTAL: [
                SourceSpec("fenix", "FENIX", "incremental", "tranfac_incremental.sql")
            ]
        }


class BronzeTranfacPipeline:
    def __init__(
            self,
            app_config: AppConfig,
            database_config: Optional[DatabaseConfig] = None,
            pipeline_config: Optional[PipelineConfig] = None
    ) -> None:
        self.database_config = database_config or DatabaseConfig(app_config)
        self.pipeline_config = pipeline_config or PipelineConfig(app_config)

    def _build_params_for_mode(self) -> Optional[dict[str, object]]:
        if self.pipeline_config.mode_pipeline == RunMode.INICIAL:
            return None
        with get_session(self.database_config.db_alias_load) as session:
            max_incremental_id = self.database_config.model_class.get_last_transaction_id(session) #Revisar xq se tendria que emviar
            # la fecha de Transaccion de Facturas y cargar primero trnafac y luego facturas para incremnetal
        return {"max_incremental_id": max_incremental_id}

    def _build_pipeline(self, spec: SourceSpec, sql_text: str, params: Optional[Dict[str, object]]) -> LoggingPipeline:
        steps = [
            ("Extract Data from Fenix Database",
             DatabaseExtractor(db_alias=spec.db_alias_load, query=sql_text, params=params)),
            ("Load DatawareHouse Bronze Tranfac", DWBatchedLoader(
                db_alias=self.database_config.db_alias_load,
                model_class=self.database_config.model_class,
                mode=self.database_config.mode,
                conflict_cols=self.database_config.conflict_cols,
                update_cols=self.database_config.update_cols,
                batch_size=self.database_config.batch_size,
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
