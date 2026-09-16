from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    brand_id: Mapped[int] = mapped_column(
        ForeignKey("brands.brand_id"),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )