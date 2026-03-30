from sqlalchemy import Column, String, DateTime, func, BigInteger, Integer
from sqlalchemy.orm import Session

from models.base import Base
from models.base_model import BaseModel


class BronzeOperatividadEntity(Base, BaseModel):
    __tablename__ = "camunda_operatividad"
    __table_args__ = {'schema': 'analytics_bronze'}

    id_operatividad = Column(BigInteger, primary_key=True)
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
    serial_firma = Column(String(50), unique=True)
    cedula = Column(String(25))
    fecha_aprobacion = Column(DateTime(timezone=False))
    factura = Column(String(50))
    ruc = Column(String(50))
    tipo_firma = Column(String(25))
    fecha_inicio_tramite = Column(DateTime(timezone=False))
    ruc_aux = Column(String(25))
    medio = Column(String(25))
    sf_control = Column(Integer)
    producto = Column(String(25))
    grupo_vendedor = Column(String(50))
