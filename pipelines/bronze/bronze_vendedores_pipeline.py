from typing import Optional, Type, List, Dict

from common.session_manager import get_session
from config.app_config import AppConfig
from config.logging_pipeline import LoggingPipeline
from entities.bronze.broze_vendedores_entity import BronzeVendedoresEntity
from etl.extract.db_extractor import DatabaseExtractor
from etl.load.db_load import DWBatchedLoader
from etl.transform.general_functions import CleanSpecialCharacters
from utils.RunMode import RunMode
from utils.general_functions import load_sql_statement
from utils.mode_persistence import ModePersistence
from utils.source_spec import SourceSpec


class DatabaseConfig:
    def __init__(self, app_config):

        self.db_alias_load: str = app_config.db_alias
        self.model_class: Type[BronzeVendedoresEntity] = BronzeVendedoresEntity
        self.mode: ModePersistence = ModePersistence.UPDATE
        self.conflict_cols: tuple[str, ...] = ('codven',)
        self.update_cols: tuple[str, ...] = ('update_date', 'nomven', 'fecha_act')
        self.batch_size: int = 3000
        self.commit_per_batch: bool = True


class PipelineConfig:
    def __init__(self, app_config):
        self.pipeline_name: str = "Bronze Vendedores Entity Pipeline"
        self.mode_pipeline: RunMode = app_config.run_mode
        self.SOURCE_BY_MODE: Dict[RunMode, List[SourceSpec]] = {
            RunMode.INICIAL: [
                SourceSpec("fenix", "FENIX", "initialization", "vendedores.sql")
            ],
            RunMode.INCREMENTAL: [
                SourceSpec("fenix", "FENIX", "incremental", "vendedores_incremental.sql")
            ]
        }


class BronzeVendedoresPipeline:
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
            max_incremental_date = self.database_config.model_class.get_last_transaction_date(session)
        return {"max_incremental_date": max_incremental_date}

    def _build_pipeline(self, spec: SourceSpec, sql_text: str, params: Optional[Dict[str, object]]) -> LoggingPipeline:
        steps = [
            ("Extract Data from Fenix Database",
             DatabaseExtractor(db_alias=spec.db_alias_load, query=sql_text, params=params)),
            ("Clean Special Characters", CleanSpecialCharacters(['codven', ])),
            ("Load DatawareHouse Bronze Vendedores", DWBatchedLoader(
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
