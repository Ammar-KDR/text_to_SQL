from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"),
        nullable=False
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    table_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    record_id: Mapped[int] = mapped_column(
        nullable=False
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )