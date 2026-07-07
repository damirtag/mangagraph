import sqlite3

from dataclasses    import dataclass
from datetime       import datetime, timezone
from typing         import Optional

# Схема повторяет ту, что создавал SQLAlchemy в версиях <= 0.2.x,
# поэтому старые .db-файлы открываются без миграции данных.
_SCHEMA = """
CREATE TABLE IF NOT EXISTS chapters (
    id INTEGER NOT NULL PRIMARY KEY,
    volume VARCHAR NOT NULL,
    chapter VARCHAR NOT NULL,
    title VARCHAR,
    url TEXT,
    mirror_url TEXT,
    created_at DATETIME,
    CONSTRAINT uq_volume_chapter UNIQUE (volume, chapter)
);

CREATE TABLE IF NOT EXISTS ToC_url (
    id INTEGER NOT NULL PRIMARY KEY,
    manga_name VARCHAR,
    url TEXT,
    mirror_url TEXT,
    path VARCHAR,
    access_token VARCHAR,
    created_at DATETIME
);
"""


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')


@dataclass
class ChapterRecord:
    volume: str
    chapter: str
    title: Optional[str]
    url: Optional[str]
    mirror_url: Optional[str]


@dataclass
class TocRecord:
    manga_name: Optional[str]
    url: Optional[str]
    mirror_url: Optional[str]
    path: Optional[str]
    access_token: Optional[str]


class MangaStorage:
    """
    SQLite-хранилище прогресса: какие главы уже опубликованы, плюс
    path/access_token оглавления, чтобы повторный запуск редактировал
    существующую Telegraph-страницу, а не создавал новую.
    """

    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        with self._conn:
            self._conn.executescript(_SCHEMA)
        self._migrate()

    def _migrate(self):
        # БД, созданные версиями < 0.2.0, не имеют колонок path/access_token
        columns = {
            row[1] for row in self._conn.execute("PRAGMA table_info('ToC_url')")
        }
        with self._conn:
            for column in ('path', 'access_token'):
                if columns and column not in columns:
                    self._conn.execute(f"ALTER TABLE ToC_url ADD COLUMN {column} TEXT")

    def close(self):
        self._conn.close()

    def __enter__(self) -> 'MangaStorage':
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    # --- Главы ---

    def get_chapter(self, volume: str, chapter: str) -> Optional[ChapterRecord]:
        row = self._conn.execute(
            "SELECT volume, chapter, title, url, mirror_url "
            "FROM chapters WHERE volume = ? AND chapter = ?",
            (volume, chapter)
        ).fetchone()
        return ChapterRecord(**dict(row)) if row else None

    def add_chapter(
        self, volume: str, chapter: str, title: str, url: str, mirror_url: str
    ):
        with self._conn:
            self._conn.execute(
                "INSERT INTO chapters (volume, chapter, title, url, mirror_url, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (volume, chapter, title, url, mirror_url, _utcnow())
            )

    # --- Оглавление ---

    def latest_toc(self) -> Optional[TocRecord]:
        row = self._conn.execute(
            "SELECT manga_name, url, mirror_url, path, access_token "
            "FROM ToC_url ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return TocRecord(**dict(row)) if row else None

    def save_toc(
        self,
        manga_name: str,
        url: str,
        mirror_url: str,
        path: str,
        access_token: str
    ):
        with self._conn:
            self._conn.execute(
                "INSERT INTO ToC_url (manga_name, url, mirror_url, path, access_token, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (manga_name, url, mirror_url, path, access_token, _utcnow())
            )
