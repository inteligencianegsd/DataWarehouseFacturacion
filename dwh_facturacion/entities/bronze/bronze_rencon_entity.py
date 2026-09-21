from sqlalchemy import Column, String, Date, DateTime, func, BigInteger, Numeric
from sqlalchemy.orm import Session

from dwh_facturacion.models.base import Base
from dwh_facturacion.models.base_model import BaseModel


class BronzeRenconEntity(Base, BaseModel):
    __tablename__ = "fenix_rencon"
    __table_args__ = {"schema": "analytics_bronze"}

    id_sec = Column(BigInteger, primary_key=True)

    creation_date = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    codcomp = Column(String(10))
    codcta = Column(String(30))
    importe = Column(Numeric)
    codasi = Column(String(10))
    fecasi = Column(Date)
    origen = Column(String(3))

    @classmethod
    def get_last_transaction_date(cls, session: Session, where_func=None):
        """
        A diferencia de las demas entidades Bronze, el cursor incremental no usa una
        columna de fecha: rencon no tiene columna de auditoria de insercion y fecasi
        (fecha contable) puede venir retroactiva en correcciones/ajustes, por lo que
        usar MAX(fecasi) arriesga perder filas nuevas con fecha contable antigua.
        id_sec es autoincrement en el origen, por lo que captura todo lo nuevo sin
        importar la fecha contable que traiga.
        """
        query = session.query(
            func.max(cls.id_sec)
        )
        if where_func:
            query = where_func(query)
        result = query.scalar()
        return result
