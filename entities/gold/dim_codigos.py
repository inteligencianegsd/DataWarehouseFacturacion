from sqlalchemy import Column, String, DateTime, func, BigInteger
from sqlalchemy.dialects.postgresql import UUID

from models.base import Base
from models.base_model import BaseModel

class DimCodigos(Base, BaseModel):
    __tablename__ = "dim_codigos"
    __table_args__ = {"schema": "analytics_gold"}
    id_codigo = Column(BigInteger, primary_key=True)
    codigo = Column(String(25), unique=True, nullable=False)
    codigo_nombre = Column(String(255))
    familia_producto = Column(String(255))
    atencion = Column(String(255))
    venta_dirigida = Column(String(255))
    concepto_1 = Column(String(255))
    concepto_2 = Column(String(255))
    plan = Column(String(255))
    vigencia = Column(String(255))
