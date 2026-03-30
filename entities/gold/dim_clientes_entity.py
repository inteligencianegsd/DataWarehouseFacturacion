from sqlalchemy import Column, String, DateTime, func, BigInteger
from sqlalchemy.dialects.postgresql import UUID

from models.base import Base
from models.base_model import BaseModel


class DimClientesEntity(Base, BaseModel):
    __tablename__ = "dim_clientes"
    __table_args__ = {"schema": "analytics_gold"}
    id_cliente = Column(BigInteger, primary_key=True)
    codigo_cliente = Column(String(10), unique=True)
    nombre_cliente = Column(String(40))
    cif = Column(String(13))