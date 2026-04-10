from sqlalchemy import Column, String, DateTime, func, BigInteger, Integer, UniqueConstraint
from sqlalchemy.orm import Session

from models.base import Base
from models.base_model import BaseModel


class BronzeOperatividadEntity(Base, BaseModel):
    __tablename__ = "camunda_operatividad"
    __table_args__ = (
        UniqueConstraint('id_tramite', 'origen', 'factura', name='uq_tramite_factura_origen'),
        {'schema': 'analytics_bronze'}
    )

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
    id_tramite = Column(Integer)
    origen = Column(String(25))
    serial_firma = Column(String(255))
    cedula = Column(String(25))
    fecha_aprobacion = Column(DateTime(timezone=False))
    factura = Column(String(255))
    ruc = Column(String(50))
    tipo_firma = Column(String(255))
    fecha_inicio_tramite = Column(DateTime(timezone=False))
    ruc_aux = Column(String(25))
    medio = Column(String(25))
    sf_control = Column(Integer)
    producto = Column(String(25))
    grupo_vendedor = Column(String(50))
    estado = Column(String(25))
    fecha_factura = Column(DateTime(timezone=False))

    @classmethod
    def get_last_approbation_date(cls, session: Session, where_func=None):
        query = session.query(
            func.max(cls.fecha_aprobacion)
        )
        if where_func:
            query = where_func(query)
        result = query.scalar()
        return str(result) if result else None

    @classmethod
    def get_last_billing_date(cls, session: Session, where_func=None):
        query = session.query(
            func.max(cls.fecha_factura )
        )
        if where_func:
            query = where_func(query)
        result = query.scalar()
        return str(result) if result else None

