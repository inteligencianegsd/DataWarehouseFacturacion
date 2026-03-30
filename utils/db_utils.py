from sqlalchemy import text

from models.base import Base
from sqlalchemy import inspect

def truncate_tables(session, tables):
    for table in tables:
        schema = table.__table__.schema
        name = table.__table__.name

        session.execute(
            text(f"TRUNCATE TABLE {schema}.{name} RESTART IDENTITY CASCADE")
        )

    session.commit()


def create_all_tables(session):
    Base.metadata.create_all(session.bind)
    inspector = inspect(session.bind)
    print(inspector.get_table_names())
