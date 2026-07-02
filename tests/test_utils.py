import pytest

from mangagraph.exceptions import InvalidURLException
from mangagraph.utils import (
    estimate_remaining_time,
    extract_slug,
    normalize_chapter_number,
    sanitize_db_name,
)


class TestExtractSlug:
    def test_manga_url(self):
        assert extract_slug(
            'https://mangalib.me/ru/manga/7965--chainsaw-man'
        ) == '7965--chainsaw-man'

    def test_manga_url_with_query(self):
        assert extract_slug(
            'https://mangalib.me/ru/manga/206--one-piece?section=info'
        ) == '206--one-piece'

    def test_reader_url(self):
        assert extract_slug(
            'https://mangalib.me/ru/7965--chainsaw-man/read/v1/c1'
        ) == '7965--chainsaw-man'

    def test_old_format_without_ru(self):
        assert extract_slug(
            'https://mangalib.me/manga/706--onepunchman'
        ) == '706--onepunchman'

    def test_wrong_domain(self):
        with pytest.raises(InvalidURLException):
            extract_slug('https://example.com/ru/manga/7965--chainsaw-man')

    def test_http_scheme(self):
        with pytest.raises(InvalidURLException):
            extract_slug('http://mangalib.me/ru/manga/7965--chainsaw-man')

    def test_no_slug(self):
        with pytest.raises(InvalidURLException):
            extract_slug('https://mangalib.me/ru/manga/')

    def test_garbage(self):
        with pytest.raises(InvalidURLException):
            extract_slug('not a url at all')


class TestNormalizeChapterNumber:
    def test_int(self):
        assert normalize_chapter_number(10) == '10'

    def test_whole_float(self):
        assert normalize_chapter_number(10.0) == '10'

    def test_half_chapter(self):
        assert normalize_chapter_number(10.5) == '10.5'

    def test_string_with_trailing_zero(self):
        assert normalize_chapter_number('10.50') == '10.5'

    def test_string_int(self):
        assert normalize_chapter_number('42') == '42'

    def test_non_numeric_passthrough(self):
        assert normalize_chapter_number('extra') == 'extra'

    def test_none(self):
        assert normalize_chapter_number(None) == ''

    def test_equivalence_across_types(self):
        # Именно так номера сравниваются между API (строки) и вводом юзера (числа)
        assert normalize_chapter_number('10.5') == normalize_chapter_number(10.5)
        assert normalize_chapter_number('10') == normalize_chapter_number(10.0)


class TestSanitizeDbName:
    def test_simple_name(self):
        assert sanitize_db_name('one-piece') == 'one-piece.db'

    def test_special_chars_replaced(self):
        result = sanitize_db_name('Ван Панчмен: сезон 2')
        assert result.endswith('.db')
        assert ':' not in result and ' ' not in result

    def test_short_name_hashed(self):
        result = sanitize_db_name('!!')
        assert result.endswith('.db')
        assert len(result) > len('.db')

    def test_underscores_only_hashed(self):
        result = sanitize_db_name('///')
        assert result != '___.db'


class TestEstimateRemainingTime:
    def test_less_than_minute(self):
        assert estimate_remaining_time(0) == 'меньше минуты'

    def test_minutes(self):
        assert 'мин' in estimate_remaining_time(100)

    def test_hours(self):
        assert 'ч' in estimate_remaining_time(5000)
