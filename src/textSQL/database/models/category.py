from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class Category(Base):
    __tablename__ = "categories"

    category_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    category_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    parent_category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.category_id"),
        nullable=True
    )