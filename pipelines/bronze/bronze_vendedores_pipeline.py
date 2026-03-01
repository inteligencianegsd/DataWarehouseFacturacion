from typing import Optional, Type, List, Dict

from common.session_manager import get_session
from config.logging_pipeline import LoggingPipeline
from entities.bronze.broze_vendedores_entity import BronzeVendedoresEntity
from etl.extract.db_extractor import DatabaseExtractor
from etl.load.db_load import DWBatchedLoader
from utils.RunMode import RunMode
from utils.general_functions import load_sql_statement
from utils.mode_persistence import ModePersistence
from utils.source_spec import SourceSpec


class DatabaseConfig:
    db_alias_load: str = "LOCAL"
    model_class: BronzeVendedoresEntity = BronzeVendedoresEntity
    mode: ModePersistence = ModePersistence.INSERT
    conflict_cols: tuple[str] = None
    batch_size: int = 3000
    commit_per_batch: bool = True


class PipelineConfig:
    pipeline_name: str = "Bronze Vendedores Entity Pipeline"
    mode_pipeline: RunMode = RunMode.INICIAL

    SOURCE_BY_MODE: Dict[RunMode, List[SourceSpec]] = {
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
            database_config: Optional[DatabaseConfig] = None,
            pipeline_config: Optional[PipelineConfig] = None
    ) -> None:
        self.database_config = database_config or DatabaseConfig()
        self.pipeline_config = pipeline_config or PipelineConfig()

    def _build_params_for_mode(self) -> Optional[dict[str, object]]:
        if self.pipeline_config.mode_pipeline == RunMode.INICIAL:
            return None
        with get_session("QUANTA") as session:
            max_emission_date = DatabaseConfig.model_class.get_last_transaction_date(session)
        return {"max_emission_date": max_emission_date}

    def _build_pipeline(self, spec: SourceSpec, sql_text: str, params: Optional[Dict[str, object]]) -> LoggingPipeline:
        steps = [
            ("Extract Data from Fenix Database",
             DatabaseExtractor(db_alias=spec.db_alias_load, query=sql_text, params=params)),
            ("Load DatawareHouse Bronze Fracturas", DWBatchedLoader(
                db_alias=self.database_config.db_alias_load,
                model_class=self.database_config.model_class,
                mode=self.database_config.mode,
                conflict_cols=self.database_config.conflict_cols,
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
