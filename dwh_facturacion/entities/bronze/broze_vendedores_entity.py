from datetime import timedelta, timezone

from sqlalchemy import Column, String, DateTime, func, BigInteger
from sqlalchemy.orm import Session

from dwh_facturacion.models.base import Base
from dwh_facturacion.models.base_model import BaseModel

# Hora local de Fenix (MariaDB con system_time_zone -05, sin horario de verano)
FENIX_TZ = timezone(timedelta(hours=-5))


class BronzeVendedoresEntity(Base, BaseModel):
    __tablename__ = "fenix_vendedores"
    __table_args__ = {"schema": "analytics_bronze"}

    id_codven = Column(BigInteger, primary_key=True)
    creation_date = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )
    update_date = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
        onupdate=func.now()
    )

    codven = Column(String(10), unique=True)
    nomven = Column(String(40))
    fecha_act = Column(DateTime(timezone=True))

    @classmethod
    def get_last_transaction_date(cls, session: Session, where_func=None):
        query = session.query(
            func.max(cls.fecha_act)
        )
        if where_func:
            query = where_func(query)
        result = query.scalar()
        if not result:
            return None
        # fecha_act es timestamptz en Bronze, pero en Fenix es DATETIME sin zona. Se pasa
        # como hora local de Fenix sin offset: MariaDB descarta el '-05:00' del literal, y
        # si la sesion de QUANTA no estuviera en -05 el watermark se correria de horas.
        if result.tzinfo is not None:
            result = result.astimezone(FENIX_TZ).replace(tzinfo=None)
        return str(result)
