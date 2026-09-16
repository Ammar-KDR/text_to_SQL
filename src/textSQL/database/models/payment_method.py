from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    payment_method_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    method_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    provider_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    method_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )