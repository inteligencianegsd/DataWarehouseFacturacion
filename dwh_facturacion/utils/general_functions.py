from importlib import resources
from pathlib import Path


def load_sql_statement(folder_name, query_name):
    sql_package = f"dwh_facturacion.include.sql.{folder_name}"
    ref = resources.files(sql_package).joinpath(query_name)
    return ref.read_text(encoding="utf-8")


def load_csv_file(filename: str) -> Path:
    ref = resources.files("dwh_facturacion.include.archivos").joinpath(filename)
    return Path(str(ref))


def list_in_string(list_objects):
    return tuple(f"'{value}'" for value in list_objects)
