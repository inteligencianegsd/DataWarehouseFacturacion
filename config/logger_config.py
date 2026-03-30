import logging

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,  # Nivel general de tu app
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("errores_sqlalchemy.log", encoding="utf-8"),  # <- descomentar para guardar los Loggs
        ],
        force=True,  # MUY IMPORTANTE: resetea config previa
    )

    # Silenciar la parte "verbosa" de SQLAlchemy
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)