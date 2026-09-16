from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"),
        primary_key=True
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.role_id"),
        primary_key=True
    )