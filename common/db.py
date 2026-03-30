from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from common.connection import build_connection_url
from config.setting import get_db_config

# Configuracion para las Bases de Datos
DB_CONFIG_PORTAL = get_db_config("PORTAL")
DB_CONFIG_LOCAL = get_db_config("LOCAL")
DB_CONFIG_FENIX = get_db_config("FENIX")
DB_CONFIG_CAMUNDA = get_db_config("CAMUNDA")
DB_CONFIG_QUANTA = get_db_config("QUANTA")
DB_CONFIG_LATINUM = get_db_config("LATINUM")
DB_CONFIG_PORTAL_GK = get_db_config("PORTAL_GK")


# Engine y session para la base principal

engine = create_engine(build_connection_url(DB_CONFIG_LOCAL), echo=False, hide_parameters=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Engine y session para la base de datos del portal
engine_portal = create_engine(build_connection_url(DB_CONFIG_PORTAL), echo=False, future=True, hide_parameters=True)
SessionPortal = sessionmaker(autocommit=False, autoflush=False, bind=engine_portal)

engine_portal_gk = create_engine(build_connection_url(DB_CONFIG_PORTAL_GK), echo=False, future=True, hide_parameters=True)
SessionPortalGk = sessionmaker(autocommit=False, autoflush=False, bind=engine_portal_gk)

# Engine y session para la base de datos del Fenix
engine_fenix = create_engine(build_connection_url(DB_CONFIG_FENIX), echo=False, hide_parameters=True)
SessionFenix = sessionmaker(autocommit=False, autoflush=False, bind=engine_fenix)

# Engine y session para la base de datos del CAMUNDA
engine_camunda = create_engine(build_connection_url(DB_CONFIG_CAMUNDA), echo=False, hide_parameters=True)
SessionCamunda = sessionmaker(autocommit=False, autoflush=False, bind=engine_camunda)

# Engine y session para la base de datos del LATINUM
engine_latinum = create_engine(build_connection_url(DB_CONFIG_LATINUM), echo=False, hide_parameters=True)
SessionLatinum = sessionmaker(autocommit=False, autoflush=False, bind=engine_latinum)

# Engine y session para la base de datos del QUANTA
engine_quanta = create_engine(build_connection_url(DB_CONFIG_QUANTA), echo=False, hide_parameters=True, connect_args={"options": "-c TimeZone=America/Guayaquil"})
SessionQuanta = sessionmaker(autocommit=False, autoflush=False, bind=engine_quanta)
