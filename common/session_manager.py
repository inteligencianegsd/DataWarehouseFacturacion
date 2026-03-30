from contextlib import contextmanager
from common.db import SessionPortal, SessionFenix, SessionCamunda, SessionQuanta, SessionLatinum, SessionLocal, \
    SessionPortalGk


# session_manager.py
@contextmanager
def get_session(db_alias="default"):
    if db_alias == "PORTAL":
        session = SessionPortal()
    elif db_alias == 'FENIX':
        session = SessionFenix()
    elif db_alias == 'CAMUNDA':
        session = SessionCamunda()
    elif db_alias == 'QUANTA':
        session = SessionQuanta()
    elif db_alias == 'LATINUM':
        session = SessionLatinum()
    elif db_alias == 'PORTAL_GK':
        session = SessionPortalGk()
    else:
        session = SessionLocal()

    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
