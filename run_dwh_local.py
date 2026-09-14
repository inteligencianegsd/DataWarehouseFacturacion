"""
Replica local (fuera de Airflow) de las tareas Python del DAG dwh_facturacion_dag.

Corre las mismas 8 tareas de extraccion (Fenix/Camunda -> Bronze/Features),
en el mismo orden que el DAG, pero escribiendo en la base LOCAL
(DB_*_LOCAL en .env) en lugar de QUANTA. Pensado como alternativa cuando
QUANTA no esta disponible.

Uso: python run_dwh_local.py
"""
import sys
import traceback

from dwh_facturacion.config.app_config import AppConfig
from dwh_facturacion.config.logger_config import setup_logger
from dwh_facturacion.utils.RunMode import RunMode

from dwh_facturacion.pipelines.features.features_facturas_exluidas_pipeline import FeaturesFacturasExcluidasPipelines
from dwh_facturacion.pipelines.bronze.bronze_operatividad_pipeline import BronzeOperatividadPipeline
from dwh_facturacion.pipelines.bronze.bronze_codigos_pipeline import BronzeCodigosPipeline
from dwh_facturacion.pipelines.bronze.bronze_articulos_pipeline import BronzeArticulosPipeline
from dwh_facturacion.pipelines.bronze.bronze_facturas_pipeline import BronzeFacturasPipeline
from dwh_facturacion.pipelines.bronze.bronze_tranfac_pipeline import BronzeTranfacPipeline
from dwh_facturacion.pipelines.bronze.bronze_clientes_pipeline import BronzeClientesPipeline
from dwh_facturacion.pipelines.bronze.bronze_vendedores_pipeline import BronzeVendedoresPipeline

DB_ALIAS = "LOCAL"
RUN_MODE = RunMode.INCREMENTAL

# Mismo orden de dependencias que dwh_facturacion_dag.py:
# init_task >> features_facturas_excluidas >> bronze_operatividad >> bronze_codigos
# >> bronze_articulos >> bronze_facturas >> bronze_tranfac >> bronze_clientes
# >> bronze_vendedores >> dbt_run
STEPS = [
    ("features_facturas_excluidas", lambda cfg: FeaturesFacturasExcluidasPipelines(cfg).run()),
    ("bronze_operatividad", lambda cfg: BronzeOperatividadPipeline(cfg).run()),
    ("bronze_codigos", lambda cfg: BronzeCodigosPipeline(cfg).run()),
    ("bronze_articulos", lambda cfg: BronzeArticulosPipeline(cfg).run()),
    ("bronze_facturas", lambda cfg: BronzeFacturasPipeline(cfg).run()),
    ("bronze_tranfac", lambda cfg: BronzeTranfacPipeline(cfg).run()),
    ("bronze_clientes", lambda cfg: BronzeClientesPipeline(cfg).run()),
    ("bronze_vendedores", lambda cfg: BronzeVendedoresPipeline(cfg).run()),
]


def main():
    setup_logger()
    app_config = AppConfig(db_alias=DB_ALIAS, run_mode=RUN_MODE)

    print(f"=== DWH Facturacion LOCAL (db_alias={DB_ALIAS}, run_mode={RUN_MODE}) ===")
    for name, step in STEPS:
        print(f"\n--- {name} ---")
        try:
            step(app_config)
            print(f"--- {name}: OK ---")
        except Exception:
            print(f"--- {name}: FALLO ---")
            traceback.print_exc()
            sys.exit(1)

    print("\n=== Todas las tareas Python completadas OK. Continuar con dbt run/test. ===")


if __name__ == "__main__":
    main()
