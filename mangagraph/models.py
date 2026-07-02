from sqlalchemy     import Column, Integer, String, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import declarative_base

from datetime       import datetime, timezone

Base = declarative_base()

def _utcnow():
    return datetime.now(timezone.utc)

class Chapter(Base):
    __tablename__ = 'chapters'
    # Номера томов/глав хранятся строками: у MangaLib бывают главы '10.5', 'extra' и т.п.
    __table_args__ = (UniqueConstraint('volume', 'chapter', name='uq_volume_chapter'),)

    id = Column(Integer, primary_key=True)
    volume = Column(String, nullable=False)
    chapter = Column(String, nullable=False)
    title = Column(String)
    url = Column(Text)
    mirror_url = Column(Text)  # Alternative URL if telegra.ph is not accessible
    created_at = Column(DateTime, default=_utcnow)

    def __repr__(self):
        return f"<Chapter(volume={self.volume}, chapter={self.chapter}, title={self.title})>"

class TocURL(Base):
    __tablename__ = 'ToC_url'

    id = Column(Integer, primary_key=True)
    manga_name = Column(String)
    url = Column(Text)
    mirror_url = Column(Text)
    # path + access_token позволяют редактировать оглавление при повторных запусках,
    # вместо создания новой страницы каждый раз
    path = Column(String)
    access_token = Column(String)
    created_at = Column(DateTime, default=_utcnow)

    def __repr__(self):
        return (
            f"<ToC_url(url={self.url}, "
            f"mirror_url={self.mirror_url}, "
            f"manga_name={self.manga_name})>"
        )
