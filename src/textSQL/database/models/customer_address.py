from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class CustomerAddress(Base):
    __tablename__ = "customer_addresses"

    address_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.customer_id"),
        nullable=False
    )

    address_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    postal_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )