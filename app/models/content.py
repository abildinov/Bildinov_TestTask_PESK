from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class ContentItem(Base):
    __tablename__ = 'content_items'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    body:Mapped[str] = mapped_column(Text)
    access_level: Mapped[str] = mapped_column(String(50), index=True)