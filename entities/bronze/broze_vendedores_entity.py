from sqlalchemy import Column, String, DateTime, func, BigInteger
from sqlalchemy.orm import Session

from models.base import Base
from models.base_model import BaseModel


class BronzeVendedoresEntity(Base, BaseModel):
    __tablename__ = "fenix_vendedores"
    __table_args__ = {"schema": "analytics_bronze"}

    id_codven = Column(BigInteger, primary_key=True)
    creation_date = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )
    update_date = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
        onupdate=func.now()
    )

    codven = Column(String(10), unique=True)
    nomven = Column(String(40))
    fecha_act = Column(DateTime(timezone=True))

    @classmethod
    def get_last_transaction_date(cls, session: Session, where_func=None):
        query = session.query(
            func.max(cls.fecha_act)
        )
        if where_func:
            query = where_func(query)
        result = query.scalar()
        return str(result) if result else None
