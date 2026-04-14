import logging
import sys

from common.session_manager import get_session
from config.app_config import AppConfig
from config.logger_config import setup_logger
from config.pipeline_config import PipelineGlobalConfig
from models.base import Base
from pipelines.bronze.bronze_clientes_pipeline import BronzeClientesPipeline
from pipelines.bronze.bronze_facturas_pipeline import BronzeFacturasPipeline
from pipelines.bronze.bronze_tranfac_pipeline import BronzeTranfacPipeline
from pipelines.bronze.bronze_vendedores_pipeline import BronzeVendedoresPipeline
from pipelines.bronze.bronze_articulos_pipeline import BronzeArticulosPipeline
from pipelines.bronze.bronze_codigos_pipeline import BronzeCodigosPipeline
from pipelines.bronze.bronze_operatividad_pipeline import BronzeOperatividadPipeline

from entities.bronze.broze_facturas_entity import BronzeFacturaEntity
from entities.bronze.bronze_clientes_entity import BronzeClienteEntity
from entities.bronze.broze_vendedores_entity import BronzeVendedoresEntity
from entities.bronze.broze_tranfac_entity import BronzeTranfacEntity
from entities.bronze.bronze_articulos_entity import BronzeArticulosEntity
from entities.bronze.bronze_codigos_entity import BronzeCodigosEntity
from entities.bronze.bronze_operatividad_entity import BronzeOperatividadEntity
from entities.gold.dim_vendedores_entity import DimVendedoresEntity
from entities.gold.dim_clientes_entity import DimClientesEntity
from entities.gold.dim_articulos_entity import DimArticulosEntity
from entities.gold.dim_facturas_entity import DimFacturasEntity
from entities.gold.dim_codigos import DimCodigos
from utils.RunMode import RunMode
from utils.db_utils import truncate_tables, create_all_tables

if __name__ == "__main__":
    setup_logger()
    log = logging.getLogger(__name__)
    log.info("Inicio Proceso Datawarehouse Facturacion BY ZALY-CB")

    app_config = AppConfig(
        db_alias="QUANTA",
        run_mode=RunMode.INICIAL
    )

    log.info(f"Modo de ejecución: {app_config.run_mode}. Ejecucion en la Base {app_config.db_alias}")

    if app_config.run_mode == RunMode.INICIAL:
        if input("Para confirmar ingrese la Base a la cual va a Afectar: ").strip() != app_config.db_alias:
            sys.exit()

        log.info("FULL LOAD: truncando tablas bronze")
        with get_session(app_config.db_alias) as session:
            truncate_tables(session, [
                # BronzeOperatividadEntity,
                # BronzeCodigosEntity,
                # BronzeArticulosEntity,
                # BronzeFacturaEntity,
                # BronzeTranfacEntity,
                # BronzeClienteEntity,
                # BronzeVendedoresEntity
            ])
            create_all_tables(session)

    BronzeOperatividadPipeline(app_config).run()
    BronzeCodigosPipeline(app_config).run()
    BronzeArticulosPipeline(app_config).run()
    BronzeFacturasPipeline(app_config).run()
    BronzeTranfacPipeline(app_config).run()
    BronzeClientesPipeline(app_config).run()
    BronzeVendedoresPipeline(app_config).run()

    # Para un  proceso mas optimo se debe rdefinir en esta script
    # db_alias_load: str = "LOCAL"
    # y el runmode
