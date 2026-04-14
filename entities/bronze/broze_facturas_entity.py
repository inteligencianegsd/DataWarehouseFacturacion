from sqlalchemy import Column, String, DateTime, func, BigInteger, Numeric
from sqlalchemy.orm import Session

from models.base import Base
from models.base_model import BaseModel


class BronzeFacturaEntity(Base, BaseModel):
    __tablename__ = "fenix_facturas"
    __table_args__ = {"schema": "analytics_bronze"}

    id_numfac = Column(BigInteger, primary_key=True)
    creation_date = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )
    numfac = Column(String(10), unique=True)
    numdoc = Column(String(10))
    cliente = Column(String(50))
    numser = Column(String(6))
    pedido = Column(String(10))
    comen1 = Column(String(200))
    comen2 = Column(String(100))
    comen3 = Column(String(70))
    subtotal = Column(Numeric)
    desc0 = Column(Numeric)
    total_iva = Column(Numeric)
    total = Column(Numeric)
    codven = Column(String(10))
    emision = Column(DateTime(timezone=False))
    fecha_hora = Column(DateTime(timezone=False))

    @classmethod
    def get_last_transaction_date(cls, session: Session, where_func=None):
        query = session.query(
            func.max(cls.fecha_hora)
        )
        if where_func:
            query = where_func(query)
        result = query.scalar()
        return str(result) if result else None





