from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user_roles import user_roles

if TYPE_CHECKING:
    from app.models.user import User



if TYPE_CHECKING:
    from app.models.role import User


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    users: Mapped[list["User"]] = relationship(
        secondary=user_roles,
        back_populates="roles",
    )

