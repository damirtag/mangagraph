import pytest

from mangagraph.cli import parse_chapter_input


class TestParseChapterInput:
    def test_single(self):
        assert parse_chapter_input('42') == [42]

    def test_half_chapter(self):
        assert parse_chapter_input('10.5') == [10.5]

    def test_comma_separated(self):
        assert parse_chapter_input('1,2,3') == [1, 2, 3]

    def test_range(self):
        assert parse_chapter_input('1-5') == [1, 2, 3, 4, 5]

    def test_mixed(self):
        assert parse_chapter_input('1,3,5-7,10') == [1, 3, 5, 6, 7, 10]

    def test_mixed_with_half_chapter(self):
        assert parse_chapter_input('1,10.5,3') == [1, 3, 10.5]

    def test_duplicates_removed(self):
        assert parse_chapter_input('1,1,2,1-3') == [1, 2, 3]

    def test_whitespace_tolerated(self):
        assert parse_chapter_input(' 1 , 2 , 3 ') == [1, 2, 3]

    def test_invalid_number(self):
        with pytest.raises(ValueError):
            parse_chapter_input('abc')

    def test_invalid_range(self):
        with pytest.raises(ValueError):
            parse_chapter_input('1-x')

    def test_float_range_rejected(self):
        with pytest.raises(ValueError):
            parse_chapter_input('1.5-3')
