import sqlite3

import pytest

from mangagraph.storage import MangaStorage, ChapterRecord, TocRecord


@pytest.fixture
def storage(tmp_path):
    with MangaStorage(str(tmp_path / 'test.db')) as db:
        yield db


class TestChapters:
    def test_missing_chapter_is_none(self, storage):
        assert storage.get_chapter('1', '1') is None

    def test_roundtrip(self, storage):
        storage.add_chapter('1', '10.5', 'Тест', 'https://telegra.ph/x', 'https://graph.org/x')
        record = storage.get_chapter('1', '10.5')
        assert record == ChapterRecord(
            volume='1',
            chapter='10.5',
            title='Тест',
            url='https://telegra.ph/x',
            mirror_url='https://graph.org/x',
        )

    def test_duplicate_volume_chapter_rejected(self, storage):
        storage.add_chapter('1', '1', 'a', 'u', 'm')
        with pytest.raises(sqlite3.IntegrityError):
            storage.add_chapter('1', '1', 'b', 'u2', 'm2')


class TestToc:
    def test_empty_db_has_no_toc(self, storage):
        assert storage.latest_toc() is None

    def test_latest_toc_returns_most_recent(self, storage):
        storage.save_toc('Манга', 'url1', 'mirror1', 'path1', 'token1')
        storage.save_toc('Манга', 'url2', 'mirror2', 'path2', 'token2')
        toc = storage.latest_toc()
        assert toc == TocRecord(
            manga_name='Манга',
            url='url2',
            mirror_url='mirror2',
            path='path2',
            access_token='token2',
        )


class TestMigration:
    def test_pre_020_db_gets_new_columns(self, tmp_path):
        # БД версий < 0.2.0: ToC_url без колонок path/access_token
        db_path = str(tmp_path / 'old.db')
        conn = sqlite3.connect(db_path)
        conn.executescript("""
            CREATE TABLE chapters (
                id INTEGER NOT NULL PRIMARY KEY,
                volume VARCHAR NOT NULL,
                chapter VARCHAR NOT NULL,
                title VARCHAR,
                url TEXT,
                mirror_url TEXT,
                created_at DATETIME,
                CONSTRAINT uq_volume_chapter UNIQUE (volume, chapter)
            );
            CREATE TABLE ToC_url (
                id INTEGER NOT NULL PRIMARY KEY,
                manga_name VARCHAR,
                url TEXT,
                mirror_url TEXT,
                created_at DATETIME
            );
            INSERT INTO ToC_url (manga_name, url, mirror_url)
            VALUES ('Old', 'url', 'mirror');
        """)
        conn.commit()
        conn.close()

        with MangaStorage(db_path) as storage:
            toc = storage.latest_toc()
            assert toc.manga_name == 'Old'
            assert toc.path is None and toc.access_token is None

            storage.save_toc('Old', 'url2', 'mirror2', 'path2', 'token2')
            assert storage.latest_toc().path == 'path2'
