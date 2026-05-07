from dataclasses import dataclass


@dataclass(frozen=True)
class SourceSpec:
    name: str
    db_alias_load: str
    folder_name: str
    query_file: str
