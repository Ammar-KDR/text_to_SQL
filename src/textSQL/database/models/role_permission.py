from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.role_id"),
        primary_key=True
    )

    permission_id: Mapped[int] = mapped_column(
        ForeignKey("permissions.permission_id"),
        primary_key=True
    )