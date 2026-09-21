from sqlalchemy import Column, String, Date, DateTime, func, BigInteger
from sqlalchemy.orm import Session

from dwh_facturacion.models.base import Base
from dwh_facturacion.models.base_model import BaseModel


class BronzeEnconEntity(Base, BaseModel):
    __tablename__ = "fenix_enccon"
    __table_args__ = {"schema": "analytics_bronze"}

    id_codasi = Column(BigInteger, primary_key=True)

    creation_date = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    codcomp = Column(String(10))
    codasi = Column(String(10))
    fecasi = Column(Date)
    fecha = Column(DateTime(timezone=False))

    @classmethod
    def get_last_transaction_date(cls, session: Session, where_func=None):
        query = session.query(
            func.max(cls.fecha)
        )
        if where_func:
            query = where_func(query)
        result = query.scalar()
        return str(result) if result else None
