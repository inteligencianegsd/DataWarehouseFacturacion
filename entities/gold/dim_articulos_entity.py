from sqlalchemy import Column, String, DateTime, func, BigInteger
from sqlalchemy.dialects.postgresql import UUID

from models.base import Base
from models.base_model import BaseModel


class DimArticulosEntity(Base, BaseModel):
    __tablename__ = "dim_articulos"
    __table_args__ = {"schema": "analytics_gold"}
    id_articulo = Column(BigInteger, primary_key=True)
    codigo_articulo = Column(String(21), unique=True)
    nombre_articulo = Column(String(100))
    vigencia = Column(String(50))
    familia = Column(String(30))
    tipo_plan = Column(String(30))