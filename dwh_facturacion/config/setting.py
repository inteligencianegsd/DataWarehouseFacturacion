import os


def get_db_config(prefix: str = "DB") -> dict:
    return {
        'engine':      os.environ.get(f"DB_ENGINE_{prefix}"),
        'driver':      os.environ.get(f"DB_DRIVER_{prefix}"),
        'host':        os.environ.get(f"DB_HOST_{prefix}"),
        'port':        os.environ.get(f"DB_PORT_{prefix}"),
        'user':        os.environ.get(f"DB_USER_{prefix}"),
        'password':    os.environ.get(f"DB_PASSWORD_{prefix}"),
        'database':    os.environ.get(f"DB_NAME_{prefix}", ""),
        'odbc_driver': os.environ.get(f"DB_ODBC_DRIVER_{prefix}"),
    }
