from dotenv import dotenv_values
from pathlib import Path


def get_db_config(prefix: str = "DB"):
    env_path = Path(__file__).resolve().parent.parent / '.venv'
    env = dotenv_values(env_path)

    # 3) Lee desde el dict
    return {
        'engine': env.get(f"DB_ENGINE_{prefix}"),
        'driver': env.get(f"DB_DRIVER_{prefix}"),
        'host': env.get(f"DB_HOST_{prefix}"),
        'port': env.get(f"DB_PORT_{prefix}"),
        'user': env.get(f"DB_USER_{prefix}"),
        'password': env.get(f"DB_PASSWORD_{prefix}"),
        'database': env.get(f"DB_NAME_{prefix}", ""),
        'odbc_driver': env.get(f"DB_ODBC_DRIVER_{prefix}")  # <-- NUEVO
    }


# Configiracion Para distintas bases de datos
DB_CONFIG_PORTAL = get_db_config("PORTAL")
DB_CONFIG_LOCAL = get_db_config("LOCAL")
DB_CONFIG_FENIX = get_db_config("FENIX")
