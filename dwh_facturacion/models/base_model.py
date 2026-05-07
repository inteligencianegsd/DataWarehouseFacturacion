from typing import Literal, Type

from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session
import pandas as pd
from sqlalchemy.dialects.postgresql import insert

from dwh_facturacion.utils.mode_persistence import ModePersistence


class BaseModel:
    """
    Clase base para modelos ORM con métodos utilitarios comunes.
    """

    def persist(self, session: Session):
        session.add(self)

    @classmethod
    def persist_multiple(cls, session: Session, objetos: list):
        session.add_all(objetos)

    @classmethod
    def search_by_id(cls, session: Session, id_):
        return session.get(cls, id_)

    """
    @classmethod
    def persist_from_dataframe(cls, session: Session, df: pd.DataFrame):
        objetos = [cls(**row.where(pd.notnull(row), None)) for _, row in df.iterrows()]
        cls.persist_multiple(session, objetos)
    """

    @classmethod
    def persist_from_dataframe(cls, session: Session, df: pd.DataFrame, conflict_cols=None,
                               mode: ModePersistence = ModePersistence.INSERT, update_cols=None):
        """
        Inserta datos desde un DataFrame.
        - conflict_cols: lista de columnas para identificar conflictos (por ejemplo, ['cod_cliente'])
        - mode: 'INSERT' (default, solo inserta), 'IGNORE' (ignora si hay conflicto), 'UPDATE' (actualiza si hay conflicto)
        - update_cols: columnas a actualizar en modo update (si None, actualiza todas excepto las de conflicto)
        """

        # Revisa Parametros basicos del tipo de insercion y en caso de ser IGNORE o UPDATE identifica
        # que exista conflict_cols para poder validar los conflictos
        if df is None or df.empty:
            raise ValueError("El Dataframe no puede estar vacio")
        if mode not in [ModePersistence.INSERT, ModePersistence.IGNORE, ModePersistence.UPDATE]:
            raise ValueError("Mode insertion invalide")
        if mode in [ModePersistence.IGNORE, ModePersistence.UPDATE] and not conflict_cols:
            raise ValueError(f"Debe especificar 'conflict_cols' para el modo {mode}")

        # Valida que elementos tiene NaN y los reemplaza por None. El Where reemplaza donde la mascara es False
        records = df.where(pd.notnull(df), None).to_dict(orient='records')

        stmt = insert(cls.__table__).values(records)

        if mode == ModePersistence.IGNORE:
            stmt = stmt.on_conflict_do_nothing(index_elements=conflict_cols)
        elif mode == ModePersistence.UPDATE:
            if update_cols is None:
                update_cols = [col for col in df.columns if col not in conflict_cols]
            update_dict = {col: getattr(stmt.excluded, col) for col in update_cols}
            stmt = stmt.on_conflict_do_update(
                index_elements=conflict_cols,
                set_=update_dict
            )

        session.execute(stmt)
        #session.commit()
