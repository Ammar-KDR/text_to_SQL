from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class ShippingMethod(Base):
    __tablename__ = "shipping_methods"

    shipping_method_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    carrier_id: Mapped[int] = mapped_column(
        ForeignKey("shipping_carriers.carrier_id"),
        nullable=False
    )

    method_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )