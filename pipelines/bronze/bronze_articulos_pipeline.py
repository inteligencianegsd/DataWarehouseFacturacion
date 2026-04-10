from typing import Optional, List, Dict, Type

from common.session_manager import get_session
from config.app_config import AppConfig
from config.logging_pipeline import LoggingPipeline
from entities.bronze.bronze_articulos_entity import BronzeArticulosEntity
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
        self.model_class: Type[BronzeArticulosEntity] = BronzeArticulosEntity
        self.mode: ModePersistence = ModePersistence.UPDATE
        self.conflict_cols: tuple[str, ...] = ('codart',)
        self.update_cols: tuple[str, ...] = ('update_date', 'nomart', 'nomart2')
        self.commit_per_batch: bool = False


class PipelineConfig:
    def __init__(self, app_config):
        self.pipeline_name: str = "Bronze Articulos Entity Pipeline"
        self.mode_pipeline: RunMode = app_config.run_mode

        self.SOURCE_BY_MODE: Dict[RunMode, List[SourceSpec]] = {
            RunMode.INICIAL: [
                SourceSpec("fenix", "FENIX", "initialization", "articulos.sql")
            ],
            RunMode.INCREMENTAL: [
                SourceSpec("fenix", "FENIX", "initialization", "articulos.sql")
            ]
        }


class BronzeArticulosPipeline:
    def __init__(
            self,
            app_config: AppConfig,
            database_config: Optional[DatabaseConfig] = None,
            pipeline_config: Optional[PipelineConfig] = None
    ) -> None:
        self.database_config = database_config or DatabaseConfig(app_config)
        self.pipeline_config = pipeline_config or PipelineConfig(app_config)

    def _build_params_for_mode(self) -> Optional[dict[str, object]]:
        return None
        # Descomentar en caso de buscar una Act. incremental en funcion de un campo
        #     max_emission_date = DatabaseConfig.model_class.get_last_transaction_date(session)
        # return {"max_emission_date": max_emission_date}

    def _build_pipeline(self, spec: SourceSpec, sql_text: str, params: Optional[Dict[str, object]]) -> LoggingPipeline:
        steps = [
            ("Extract Data from Fenix Database",
             DatabaseExtractor(db_alias=spec.db_alias_load, query=sql_text, params=params)),
            ("Clean Special Characters", CleanSpecialCharacters(['nomart', 'nomart2'])),
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
