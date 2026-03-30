from sqlalchemy import Column, String, DateTime, func, BigInteger
from sqlalchemy.dialects.postgresql import UUID

from models.base import Base
from models.base_model import BaseModel


class DimFacturasEntity(Base, BaseModel):
    __tablename__ = "dim_facturas"
    __table_args__ = {"schema": "analytics_gold"}

    id_factura = Column(BigInteger, primary_key=True)
    codigo_factura = Column(String(10))
    codigo_documento = Column(String(10))
    numero_factura = Column(String(16))
    comentario_1 = Column(String(200))
    comentario_2 = Column(String(100))
    comentario_3 = Column(String(70))
    codigo_descuento = Column(String(30))
    estado_factura = Column(String(15))
    grupo_vendedor = Column(String(100))
    tipo_venta = Column(String(20))


