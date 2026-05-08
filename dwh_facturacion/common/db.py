from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dwh_facturacion.common.connection import build_connection_url
from dwh_facturacion.config.setting import get_db_config

_engine_cache: dict = {}
_session_cache: dict = {}

_CONNECT_ARGS = {
    "QUANTA": {"connect_args": {"options": "-c TimeZone=America/Guayaquil"}},
}


def get_engine(prefix: str):
    if prefix not in _engine_cache:
        config = get_db_config(prefix)
        url = build_connection_url(config)
        extra = _CONNECT_ARGS.get(prefix, {})
        _engine_cache[prefix] = create_engine(url, echo=False, hide_parameters=True, **extra)
    return _engine_cache[prefix]


def get_session_maker(prefix: str):
    if prefix not in _session_cache:
        _session_cache[prefix] = sessionmaker(
            autocommit=False, autoflush=False, bind=get_engine(prefix)
        )
    return _session_cache[prefix]


# Aliases para compatibilidad con session_manager.py
def SessionLocal():   return get_session_maker("LOCAL")()
def SessionPortal():  return get_session_maker("PORTAL")()
def SessionPortalGk(): return get_session_maker("PORTAL_GK")()
def SessionFenix():   return get_session_maker("FENIX")()
def SessionCamunda(): return get_session_maker("CAMUNDA")()
def SessionLatinum(): return get_session_maker("LATINUM")()
def SessionQuanta():  return get_session_maker("QUANTA")()
