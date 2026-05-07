from sqlalchemy import Column, String, DateTime, func, BigInteger

from sqlalchemy.orm import Session

from dwh_facturacion.models.base import Base
from dwh_facturacion.models.base_model import BaseModel


class FeaturesFacturasExcluidasEntity(Base, BaseModel):
    __tablename__ = "facturas_excluidas"
    __table_args__ = {"schema": "analytics_features"}
    # id_factura_exluida = Column(BigInteger, primary_key=True)
    codigo_factura = Column(String, primary_key=True)
    motivo = Column(String(150))

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
