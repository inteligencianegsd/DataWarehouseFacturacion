from sqlalchemy import Column, String, DateTime, func, BigInteger
from sqlalchemy.orm import Session

from models.base import Base
from models.base_model import BaseModel


class BronzeClienteEntity(Base, BaseModel):
    __tablename__ = "fenix_clientes"
    __table_args__ = {"schema": "analytics_bronze"}

    # id_codcli = Column(BigInteger, primary_key=True)

    creation_date = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    update_date = Column(
        DateTime(timezone=False),
        server_default=func.now(),  # Valor inicial al crear
        onupdate=func.now(),  # Se actualiza en cada UPDATE
        nullable=False
    )

    codcli = Column(String(50), primary_key=True)
    nomcli = Column(String(100))
    cif = Column(String(13))
    fecha_act = Column(DateTime(timezone=False))

    @classmethod
    def get_last_transaction_date(cls, session: Session, where_func=None):
        query = session.query(
            func.max(cls.fecha_act)
        )
        if where_func:
            query = where_func(query)
        result = query.scalar()
        return str(result) if result else None
