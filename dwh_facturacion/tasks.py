"""
Funciones de tarea para orquestación con Apache Airflow.

Cada función encapsula un pipeline ETL del Data Warehouse de Facturación.
Pueden ser usadas directamente como callables en PythonOperator o con el
decorador @task de TaskFlow API.

Parámetros comunes:
    db_alias (str):   Base de datos destino. Valores válidos: "QUANTA", "LOCAL".
    run_mode (RunMode): Modo de ejecución.
                        RunMode.INCREMENTAL — sólo registros nuevos/modificados.
                        RunMode.INICIAL     — carga completa (full load).

Ejemplo de uso en un DAG de Airflow:

    from dwh_facturacion.tasks import (
        run_bronze_facturas,
        run_bronze_clientes,
        run_bronze_vendedores,
        run_bronze_tranfac,
        run_bronze_articulos,
        run_bronze_codigos,
        run_bronze_operatividad,
        run_features_facturas_excluidas,
    )
    from dwh_facturacion.utils.RunMode import RunMode

    with DAG("dwh_facturacion", ...) as dag:

        # TaskFlow API
        @task
        def ingest_facturas():
            run_bronze_facturas(db_alias="QUANTA", run_mode=RunMode.INCREMENTAL)

        # PythonOperator
        ingest_clientes = PythonOperator(
            task_id="ingest_clientes",
            python_callable=run_bronze_clientes,
            op_kwargs={"db_alias": "QUANTA", "run_mode": RunMode.INCREMENTAL},
        )
"""

from typing import Literal

from dwh_facturacion.config.app_config import AppConfig
from dwh_facturacion.config.logger_config import setup_logger
from dwh_facturacion.utils.RunMode import RunMode

DBAliasType = Literal["QUANTA", "LOCAL"]

_LOGGER_INITIALIZED = False


def _get_app_config(db_alias: DBAliasType, run_mode: RunMode) -> AppConfig:
    global _LOGGER_INITIALIZED
    if not _LOGGER_INITIALIZED:
        setup_logger()
        _LOGGER_INITIALIZED = True
    return AppConfig(db_alias=db_alias, run_mode=run_mode)


# ---------------------------------------------------------------------------
# Features
# ---------------------------------------------------------------------------

def run_features_facturas_excluidas(
    db_alias: DBAliasType = "QUANTA",
    run_mode: RunMode = RunMode.INCREMENTAL,
) -> None:
    """Carga la tabla features.facturas_excluidas.

    - INCREMENTAL: extrae nuevas facturas excluidas desde la base FENIX.
    - INICIAL:     carga desde el archivo CSV de referencia.
    """
    from dwh_facturacion.pipelines.features.features_facturas_exluidas_pipeline import (
        FeaturesFacturasExcluidasPipelines,
    )
    app_config = _get_app_config(db_alias, run_mode)
    FeaturesFacturasExcluidasPipelines(app_config).run()


# ---------------------------------------------------------------------------
# Bronze — FENIX
# ---------------------------------------------------------------------------

def run_bronze_facturas(
    db_alias: DBAliasType = "QUANTA",
    run_mode: RunMode = RunMode.INCREMENTAL,
) -> None:
    """Carga la tabla bronze.fenix_facturas.

    - INCREMENTAL: facturas con fecha de emisión posterior a la última cargada.
    - INICIAL:     carga histórica completa desde FENIX.
    """
    from dwh_facturacion.pipelines.bronze.bronze_facturas_pipeline import BronzeFacturasPipeline
    app_config = _get_app_config(db_alias, run_mode)
    BronzeFacturasPipeline(app_config).run()


def run_bronze_clientes(
    db_alias: DBAliasType = "QUANTA",
    run_mode: RunMode = RunMode.INCREMENTAL,
) -> None:
    """Carga la tabla bronze.fenix_clientes.

    - INCREMENTAL: clientes modificados desde la última carga.
    - INICIAL:     carga completa del catálogo de clientes desde FENIX.
    """
    from dwh_facturacion.pipelines.bronze.bronze_clientes_pipeline import BronzeClientesPipeline
    app_config = _get_app_config(db_alias, run_mode)
    BronzeClientesPipeline(app_config).run()


def run_bronze_vendedores(
    db_alias: DBAliasType = "QUANTA",
    run_mode: RunMode = RunMode.INCREMENTAL,
) -> None:
    """Carga la tabla bronze.fenix_vendedores.

    - INCREMENTAL: vendedores modificados desde la última carga.
    - INICIAL:     carga completa del catálogo de vendedores desde FENIX.
    """
    from dwh_facturacion.pipelines.bronze.bronze_vendedores_pipeline import BronzeVendedoresPipeline
    app_config = _get_app_config(db_alias, run_mode)
    BronzeVendedoresPipeline(app_config).run()


def run_bronze_tranfac(
    db_alias: DBAliasType = "QUANTA",
    run_mode: RunMode = RunMode.INCREMENTAL,
) -> None:
    """Carga la tabla bronze.fenix_tranfac (transacciones de factura).

    - INCREMENTAL: transacciones nuevas desde la última carga.
    - INICIAL:     carga histórica completa desde FENIX.
    """
    from dwh_facturacion.pipelines.bronze.bronze_tranfac_pipeline import BronzeTranfacPipeline
    app_config = _get_app_config(db_alias, run_mode)
    BronzeTranfacPipeline(app_config).run()


def run_bronze_articulos(
    db_alias: DBAliasType = "QUANTA",
    run_mode: RunMode = RunMode.INCREMENTAL,
) -> None:
    """Carga la tabla bronze.fenix_articulos.

    - INCREMENTAL: artículos modificados desde la última carga.
    - INICIAL:     carga completa del catálogo de artículos desde FENIX.
    """
    from dwh_facturacion.pipelines.bronze.bronze_articulos_pipeline import BronzeArticulosPipeline
    app_config = _get_app_config(db_alias, run_mode)
    BronzeArticulosPipeline(app_config).run()


def run_bronze_codigos(
    db_alias: DBAliasType = "QUANTA",
    run_mode: RunMode = RunMode.INCREMENTAL,
) -> None:
    """Carga la tabla bronze.fenix_codigos desde el CSV de referencia.

    El pipeline verifica si ya existen registros antes de cargar; si la tabla
    tiene datos la ejecución es un no-op (el CSV es la fuente de verdad).
    El parámetro run_mode se acepta por consistencia de firma pero no altera
    el comportamiento de este pipeline.
    """
    from dwh_facturacion.pipelines.bronze.bronze_codigos_pipeline import BronzeCodigosPipeline
    app_config = _get_app_config(db_alias, run_mode)
    BronzeCodigosPipeline(app_config).run()


# ---------------------------------------------------------------------------
# Bronze — CAMUNDA
# ---------------------------------------------------------------------------

def run_bronze_operatividad(
    db_alias: DBAliasType = "QUANTA",
    run_mode: RunMode = RunMode.INCREMENTAL,
) -> None:
    """Carga la tabla bronze.camunda_operatividad.

    - INCREMENTAL: registros de operatividad desde la última fecha cargada.
    - INICIAL:     carga histórica completa desde CAMUNDA.
    """
    from dwh_facturacion.pipelines.bronze.bronze_operatividad_pipeline import BronzeOperatividadPipeline
    app_config = _get_app_config(db_alias, run_mode)
    BronzeOperatividadPipeline(app_config).run()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def run_health_check(to_email: str) -> None:
    """Envía un correo con la versión instalada del paquete.

    Variables de entorno requeridas:
        SMTP_HOST     — servidor SMTP (ej. smtp.gmail.com)
        SMTP_PORT     — puerto (ej. 587)
        SMTP_USER     — correo remitente
        SMTP_PASSWORD — contraseña o app password
    """
    import os
    import smtplib
    from datetime import datetime
    from email.mime.text import MIMEText
    from importlib.metadata import version, PackageNotFoundError

    try:
        pkg_version = version("dwh-facturacion")
    except PackageNotFoundError:
        pkg_version = "desconocida (paquete no instalado via pip)"

    body = (
        f"Health check — DWH Facturación\n"
        f"{'─' * 40}\n"
        f"Versión instalada : {pkg_version}\n"
        f"Fecha/hora        : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Estado            : OK\n"
    )

    msg = MIMEText(body)
    msg["Subject"] = f"[DWH Facturación] Health check OK — v{pkg_version}"
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = to_email

    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"])) as server:
        server.starttls()
        server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        server.sendmail(os.environ["SMTP_USER"], to_email, msg.as_string())