from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class ShipmentItem(Base):
    __tablename__ = "shipment_items"

    shipment_id: Mapped[int] = mapped_column(
        ForeignKey("shipments.shipment_id"),
        primary_key=True
    )

    order_item_id: Mapped[int] = mapped_column(
        ForeignKey("order_items.order_item_id"),
        primary_key=True
    )

    quantity: Mapped[int] = mapped_column(
        nullable=False
    )