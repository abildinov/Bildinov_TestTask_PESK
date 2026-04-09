from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user_roles import user_roles

if TYPE_CHECKING:
    from app.models.role import Role

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    roles: Mapped[list["Role"]] = relationship(
        secondary=user_roles,
        back_populates="users",
    )
