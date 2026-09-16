from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class Warehouse(Base):
    __tablename__ = "warehouses"

    warehouse_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    warehouse_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    location: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )