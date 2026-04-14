from models.base import Base
from models.base_model import BaseModel
from sqlalchemy.orm import Session

from sqlalchemy import Column, Integer, String, DateTime, func, BigInteger, Numeric


class BronzeTranfacEntity(Base, BaseModel):
    __tablename__ = "fenix_tranfac"
    __table_args__ = {"schema": "analytics_bronze"}

    id_tranfac = Column(BigInteger, primary_key=True)
    creation_date = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    update_date = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    unico = Column(String(10), primary_key=True)
    numfac = Column(String(10))
    codart = Column(String(21))
    cantidad_d = Column(Integer)
    precio = Column(Numeric)
    desct = Column(Numeric)
    iva = Column(Numeric)

    @classmethod
    def get_last_transaction_id(cls, session: Session, where_func=None):
        query = session.query(
            func.max(cls.id_tranfac)
        )
        if where_func:
            query = where_func(query)
        result = query.scalar()
        return result if result else None

