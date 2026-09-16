from decimal import Decimal

from sqlalchemy import String, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class ProductVariant(Base):
    __tablename__ = "product_variants"

    variant_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.product_id"),
        nullable=False
    )

    sku: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    size: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    color: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )