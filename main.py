import logging

from sqlalchemy import inspect

from common.session_manager import get_session
from config.logger_config import setup_logger
from models.base import Base
from pipelines.bronze.bronze_clientes_pipeline import BronzeClientesPipeline
from pipelines.bronze.bronze_facturas_pipeline import BronzeFacturasPipeline
from pipelines.bronze.bronze_tranfac_pipeline import BronzeTranfacPipeline
from pipelines.bronze.bronze_vendedores_pipeline import BronzeVendedoresPipeline

from entities.bronze.broze_facturas_entity import BronzeFacturaEntity
from entities.bronze.bronze_clientes_entity import BronzeClienteEntity
from entities.bronze.broze_vendedores_entity import BronzeVendedoresEntity
from entities.bronze.broze_tranfac_entity import BronzeTranfacEntity


def create_all_tables():
    with get_session("LOCAL") as session:
        Base.metadata.create_all(session.bind)
        inspector = inspect(session.bind)
        print(inspector.get_table_names())


create_all_tables()

if __name__ == "__main__":
    setup_logger()
    log = logging.getLogger(__name__)
    log.info("Inicio Proceso Datawarehouse Facturacion BY ZALY-CB")

    BronzeFacturasPipeline().run()
    BronzeClientesPipeline().run()
    BronzeTranfacPipeline().run()
    BronzeVendedoresPipeline().run()
