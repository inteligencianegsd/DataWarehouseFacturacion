from sqlalchemy import Column, String, DateTime, func, BigInteger
from sqlalchemy.dialects.postgresql import UUID

from models.base import Base
from models.base_model import BaseModel


class DimVendedoresEntity(Base, BaseModel):
    __tablename__ = "dim_vendedores"
    __table_args__ = {"schema": "analytics_gold"}

    id_vendedor = Column(BigInteger, primary_key=True)
    codigo_vendedor = Column(String(10), unique=True)
    nombre_vendedor = Column(String(40))
