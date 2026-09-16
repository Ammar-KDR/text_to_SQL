from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class ProductCategory(Base):
    __tablename__ = "product_categories"

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.product_id"),
        primary_key=True
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.category_id"),
        primary_key=True
    )