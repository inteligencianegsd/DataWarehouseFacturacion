from typing import Optional, Type, List, Dict

from common.session_manager import get_session
from config.app_config import AppConfig
from config.logging_pipeline import LoggingPipeline
from entities.bronze.bronze_codigos_entity import BronzeCodigosEntity
from etl.extract.db_extractor import DatabaseExtractor
from etl.load.csv_load import CsvLoad
from etl.load.db_load import DWBatchedLoader
from etl.transform.general_functions import CleanSpecialCharacters
from utils.RunMode import RunMode
from utils.general_functions import load_sql_statement
from utils.mode_persistence import ModePersistence
from utils.source_spec import SourceSpec


class DatabaseConfig:
    def __init__(self, app_config):
        self.db_alias_load: str = app_config.db_alias
        self.model_class: Type[BronzeCodigosEntity] = BronzeCodigosEntity
        self.mode: ModePersistence = ModePersistence.UPDATE
        self.commit_per_batch: bool = False
        self.conflict_cols: tuple[str, ...] = ('codigo',)
        self.update_cols: tuple[str, ...] = (
            'update_date',
            'codigo',
            'codigo_nombre',
            'familia_producto',
            'atencion',
            'venta_dirigida',
            'concepto_1',
            'concepto_2',
            'plan',
            'vigencia'
        )


class PipelineConfig:
    pipeline_name: str = "Bronze Codigos Entity Pipeline"
    path_csv_codigos = 'include/archivos/codigos_comen3.csv'


class BronzeCodigosPipeline:
    def __init__(
            self,
            app_config: AppConfig,
            database_config: Optional[DatabaseConfig] = None,
            pipeline_config: Optional[PipelineConfig] = None
    ) -> None:
        self.database_config = database_config or DatabaseConfig(app_config)
        self.pipeline_config = pipeline_config or PipelineConfig()

    def _build_pipeline(self, path_csv_codigos) -> LoggingPipeline:
        steps = [
            ("Extract Information from csv", CsvLoad(path_csv_codigos)),
            ("Clean Special Characters", CleanSpecialCharacters([
                'codigo_nombre',
                'familia_producto',
                'atencion',
                'venta_dirigida',
                'concepto_1',
                'concepto_2',
                'plan',
                'vigencia'
            ])),
            ("Load DatawareHouse Bronze Codigos", DWBatchedLoader(
                db_alias=self.database_config.db_alias_load,
                model_class=self.database_config.model_class,
                mode=self.database_config.mode,
                commit_per_batch=self.database_config.commit_per_batch,
                conflict_cols=self.database_config.conflict_cols,
                update_cols=self.database_config.update_cols
            ))

        ]
        return LoggingPipeline(steps, pipeline_name=self.pipeline_config.pipeline_name)

    def _record_exist(self):
        with get_session(self.database_config.db_alias_load) as session:
            return session.query(BronzeCodigosEntity).first() is not None

    def run(self):
        """
        Ejecuta el pipeline.
        """
        if self._record_exist():
            return None
        else:
            pipe = self._build_pipeline(self.pipeline_config.path_csv_codigos)
            pipe.fit_transform(None)
