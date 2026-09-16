from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class Brand(Base):
    __tablename__ = "brands"

    brand_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    brand_name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )