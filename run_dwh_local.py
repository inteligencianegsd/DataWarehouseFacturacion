"""
Replica local (fuera de Airflow) de las tareas Python del DAG dwh_facturacion_dag.

Llama las mismas funciones de dwh_facturacion.tasks que usa el DAG de Airflow
(dwh_facturacion.tasks.run_*), en el mismo orden, pero con db_alias="LOCAL"
para escribir en la base local (DB_*_LOCAL en .env) en lugar de QUANTA.
Reutilizar tasks.py en vez de reconstruir los pipelines aqui garantiza que
esta corrida local se comporte igual que la corrida real en Airflow/Docker
(.76): cualquier cambio en la firma o logica de una tarea se refleja aqui
automaticamente. Pensado como alternativa cuando QUANTA no esta disponible.

Uso: python run_dwh_local.py
"""
import sys
import traceback

from dwh_facturacion.utils.RunMode import RunMode
from dwh_facturacion.tasks import (
    run_features_facturas_excluidas,
    run_bronze_operatividad,
    run_bronze_codigos,
    run_bronze_articulos,
    run_bronze_facturas,
    run_bronze_tranfac,
    run_bronze_clientes,
    run_bronze_vendedores,
    run_bronze_rencon,
    run_bronze_enccon,
)

DB_ALIAS = "LOCAL"
RUN_MODE = RunMode.INCREMENTAL

# Mismo orden de dependencias que dwh_facturacion_dag.py:
# init_task >> features_facturas_excluidas >> bronze_operatividad >> bronze_codigos
# >> bronze_articulos >> bronze_facturas >> bronze_tranfac >> bronze_clientes
# >> bronze_vendedores >> bronze_rencon >> bronze_enccon >> dbt_run
STEPS = [
    ("features_facturas_excluidas", run_features_facturas_excluidas),
    ("bronze_operatividad", run_bronze_operatividad),
    ("bronze_codigos", run_bronze_codigos),
    ("bronze_articulos", run_bronze_articulos),
    ("bronze_facturas", run_bronze_facturas),
    ("bronze_tranfac", run_bronze_tranfac),
    ("bronze_clientes", run_bronze_clientes),
    ("bronze_vendedores", run_bronze_vendedores),
    ("bronze_rencon", run_bronze_rencon),
    ("bronze_enccon", run_bronze_enccon),
]


def main():
    print(f"=== DWH Facturacion LOCAL (db_alias={DB_ALIAS}, run_mode={RUN_MODE}) ===")
    for name, step in STEPS:
        print(f"\n--- {name} ---")
        try:
            step(db_alias=DB_ALIAS, run_mode=RUN_MODE)
            print(f"--- {name}: OK ---")
        except Exception:
            print(f"--- {name}: FALLO ---")
            traceback.print_exc()
            sys.exit(1)

    print("\n=== Todas las tareas Python completadas OK. Continuar con dbt run/test. ===")


if __name__ == "__main__":
    main()
