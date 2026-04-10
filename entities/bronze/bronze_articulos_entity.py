from sqlalchemy import Column, String, DateTime, func, BigInteger

from sqlalchemy.orm import Session

from models.base import Base
from models.base_model import BaseModel


class BronzeArticulosEntity(Base, BaseModel):
    __tablename__ = "fenix_articulos"
    __table_args__ = {"schema": "analytics_bronze"}
    id_codart = Column(BigInteger, primary_key=True)
    creation_date = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False
    )

    update_date = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
        onupdate=func.now()
    )

    codart = Column(String(21), unique=True)
    nomart = Column(String(100))
    nomart2 = Column(String(50))
