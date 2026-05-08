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

import os
from typing import Literal

from dwh_facturacion.config.app_config import AppConfig
from dwh_facturacion.config.logger_config import setup_logger
from dwh_facturacion.utils.RunMode import RunMode

from dwh_facturacion.pipelines.bronze.bronze_operatividad_pipeline import BronzeOperatividadPipeline
from dwh_facturacion.pipelines.bronze.bronze_facturas_pipeline import BronzeFacturasPipeline
from dwh_facturacion.pipelines.bronze.bronze_clientes_pipeline import BronzeClientesPipeline
from dwh_facturacion.pipelines.features.features_facturas_exluidas_pipeline import FeaturesFacturasExcluidasPipelines
from dwh_facturacion.pipelines.bronze.bronze_vendedores_pipeline import BronzeVendedoresPipeline
from dwh_facturacion.pipelines.bronze.bronze_tranfac_pipeline import BronzeTranfacPipeline
from dwh_facturacion.pipelines.bronze.bronze_articulos_pipeline import BronzeArticulosPipeline
from dwh_facturacion.pipelines.bronze.bronze_codigos_pipeline import BronzeCodigosPipeline

from airflow.hooks.base import BaseHook

import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from importlib.metadata import version, PackageNotFoundError

DBAliasType = Literal["QUANTA", "LOCAL"]

_LOGGER_INITIALIZED = False


_CONN_MAP: dict[str, str] = {}


def set_conn_map(conn_map: dict[str, str]) -> None:
    """Define el mapeo prefijo → conn_id de Airflow una sola vez a nivel de módulo.

    Llamar esto al inicio del DAG (fuera de cualquier task):

        set_conn_map({
            "FENIX":   "fenix_db",
            "CAMUNDA": "camunda_db",
            "QUANTA":  "quanta_db",
        })
    """
    global _CONN_MAP
    _CONN_MAP = conn_map


def _get_app_config(db_alias: DBAliasType, run_mode: RunMode) -> AppConfig:
    global _LOGGER_INITIALIZED
    if not _LOGGER_INITIALIZED:
        setup_logger()
        _LOGGER_INITIALIZED = True
    if _CONN_MAP:
        configure_from_airflow_connections(_CONN_MAP)
    return AppConfig(db_alias=db_alias, run_mode=run_mode)


# ---------------------------------------------------------------------------
# Configuración de conexiones desde Airflow UI
# ---------------------------------------------------------------------------

def configure_from_airflow_connections(conn_map: dict[str, str]) -> None:
    """Extrae conexiones de la UI de Airflow y las inyecta como env vars
    para que get_db_config() las encuentre al momento de correr cada task.

    Args:
        conn_map: dict que mapea prefijo → conn_id de Airflow.

    Ejemplo en el DAG:
        configure_from_airflow_connections({
            "FENIX":   "fenix_db",
            "CAMUNDA": "camunda_db",
            "QUANTA":  "quanta_db",
        })
    """
    

    for prefix, conn_id in conn_map.items():
        conn = BaseHook.get_connection(conn_id)
        extra = conn.extra_dejson or {}

        os.environ[f"DB_HOST_{prefix}"]     = conn.host or ""
        os.environ[f"DB_PORT_{prefix}"]     = str(conn.port or "")
        os.environ[f"DB_USER_{prefix}"]     = conn.login or ""
        os.environ[f"DB_PASSWORD_{prefix}"] = conn.password or ""
        os.environ[f"DB_NAME_{prefix}"]     = conn.schema or ""
        os.environ[f"DB_ENGINE_{prefix}"]   = extra.get("engine", "")
        os.environ[f"DB_DRIVER_{prefix}"]   = extra.get("driver", "")
        os.environ[f"DB_ODBC_DRIVER_{prefix}"] = extra.get("odbc_driver", "")


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

    app_config = _get_app_config(db_alias, run_mode)
    BronzeOperatividadPipeline(app_config).run()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def run_health_check(
    to_email: str,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    mail_from: str,
) -> None:
    """Envía un correo con la versión instalada del paquete.

    Args:
        to_email      : destinatario del correo.
        smtp_host     : servidor SMTP (ej. smtp-relay.brevo.com).
        smtp_port     : puerto SMTP (ej. 587).
        smtp_user     : usuario SMTP de Brevo (ej. 9c35cb001@smtp-brevo.com).
        smtp_password : contraseña SMTP de Brevo.
        mail_from     : dirección visible en el campo From (ej. crisbenalcazar99@gmail.com).
    """


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
    msg["From"] = mail_from
    msg["To"] = to_email

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(mail_from, to_email, msg.as_string())