"""
Punto de entrada para ejecución local / desarrollo.

Para producción usa las funciones de dwh_facturacion.tasks directamente
desde el DAG de Airflow.
"""
import logging
import sys

from dwh_facturacion.common.session_manager import get_session
from dwh_facturacion.config.app_config import AppConfig
from dwh_facturacion.config.logger_config import setup_logger
from dwh_facturacion.entities.bronze.broze_facturas_entity import BronzeFacturaEntity
from dwh_facturacion.entities.bronze.bronze_clientes_entity import BronzeClienteEntity
from dwh_facturacion.entities.bronze.broze_vendedores_entity import BronzeVendedoresEntity
from dwh_facturacion.entities.bronze.broze_tranfac_entity import BronzeTranfacEntity
from dwh_facturacion.entities.bronze.bronze_articulos_entity import BronzeArticulosEntity
from dwh_facturacion.entities.bronze.bronze_codigos_entity import BronzeCodigosEntity
from dwh_facturacion.entities.bronze.bronze_operatividad_entity import BronzeOperatividadEntity
from dwh_facturacion.entities.gold.dim_vendedores_entity import DimVendedoresEntity
from dwh_facturacion.entities.gold.dim_clientes_entity import DimClientesEntity
from dwh_facturacion.entities.gold.dim_articulos_entity import DimArticulosEntity
from dwh_facturacion.entities.gold.dim_facturas_entity import DimFacturasEntity
from dwh_facturacion.entities.gold.dim_codigos import DimCodigos
from dwh_facturacion.entities.features.facturas_excluidas_entity import FeaturesFacturasExcluidasEntity
from dwh_facturacion.utils.RunMode import RunMode
from dwh_facturacion.utils.db_utils import truncate_tables, create_all_tables
from dwh_facturacion.tasks import (
    run_features_facturas_excluidas,
    run_bronze_operatividad,
    run_bronze_codigos,
    run_bronze_articulos,
    run_bronze_facturas,
    run_bronze_tranfac,
    run_bronze_clientes,
    run_bronze_vendedores,
)

if __name__ == "__main__":
    setup_logger()
    log = logging.getLogger(__name__)
    log.info("Inicio Proceso Datawarehouse Facturacion BY ZALY-CB")

    DB_ALIAS = "QUANTA"
    RUN_MODE = RunMode.INCREMENTAL

    log.info(f"Modo de ejecución: {RUN_MODE}. Ejecucion en la Base {DB_ALIAS}")

    if RUN_MODE == RunMode.INICIAL:
        if input("Para confirmar ingrese la Base a la cual va a Afectar: ").strip() != DB_ALIAS:
            sys.exit()

        log.info("FULL LOAD: truncando tablas bronze")
        app_config = AppConfig(db_alias=DB_ALIAS, run_mode=RunMode.INICIAL)
        with get_session(DB_ALIAS) as session:
            truncate_tables(session, [
                # BronzeOperatividadEntity,
                # BronzeCodigosEntity,
                # BronzeArticulosEntity,
                # BronzeFacturaEntity,
                # BronzeTranfacEntity,
                # BronzeClienteEntity,
                # BronzeVendedoresEntity,
            ])
            create_all_tables(session)

    run_features_facturas_excluidas(db_alias=DB_ALIAS, run_mode=RUN_MODE)
    run_bronze_operatividad(db_alias=DB_ALIAS, run_mode=RUN_MODE)
    run_bronze_codigos(db_alias=DB_ALIAS, run_mode=RUN_MODE)
    run_bronze_articulos(db_alias=DB_ALIAS, run_mode=RUN_MODE)
    run_bronze_facturas(db_alias=DB_ALIAS, run_mode=RUN_MODE)
    run_bronze_tranfac(db_alias=DB_ALIAS, run_mode=RUN_MODE)
    run_bronze_clientes(db_alias=DB_ALIAS, run_mode=RUN_MODE)
    run_bronze_vendedores(db_alias=DB_ALIAS, run_mode=RUN_MODE)