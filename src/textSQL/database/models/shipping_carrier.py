from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class ShippingCarrier(Base):
    __tablename__ = "shipping_carriers"

    carrier_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    carrier_name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )