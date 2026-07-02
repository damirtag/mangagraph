import asyncio

import pytest

from mangagraph.client import MangaLibClient
from mangagraph.constants import BASE_IMG_URL


def make_client(canned_responses):
    """Клиент с подмененным _request: endpoint -> canned payload."""
    client = MangaLibClient(token='test-token')
    calls = []

    async def fake_request(endpoint, params=None):
        calls.append((endpoint, params))
        return canned_responses[endpoint]

    client._request = fake_request
    client.calls = calls
    return client


def run(coro):
    return asyncio.run(coro)


class TestGetManga:
    def test_manga_name_prefers_rus_name(self):
        client = make_client({
            'manga/1--test': {'data': {'rus_name': 'Тест', 'name': 'Test'}}
        })
        assert run(client.get_manga_name('1--test')) == 'Тест'

    def test_manga_name_falls_back_to_name(self):
        client = make_client({
            'manga/1--test': {'data': {'rus_name': None, 'name': 'Test'}}
        })
        assert run(client.get_manga_name('1--test')) == 'Test'

    def test_manga_name_unknown_when_empty(self):
        client = make_client({'manga/1--test': {'data': {}}})
        assert run(client.get_manga_name('1--test')) == 'Unknown'


class TestGetChapters:
    payload = {
        'data': [
            {'number': '1', 'volume': '1', 'name': 'Начало'},
            {'number': '10.5', 'volume': '2', 'name': None},
        ]
    }

    def test_all_chapters(self):
        client = make_client({'manga/1--test/chapters': self.payload})
        assert len(run(client.get_chapters('1--test'))) == 2

    def test_filter_by_number(self):
        client = make_client({'manga/1--test/chapters': self.payload})
        result = run(client.get_chapters('1--test', chapter_num=1))
        assert len(result) == 1 and result[0]['number'] == '1'

    def test_filter_half_chapter_as_float(self):
        client = make_client({'manga/1--test/chapters': self.payload})
        result = run(client.get_chapters('1--test', chapter_num=10.5))
        assert len(result) == 1 and result[0]['number'] == '10.5'

    def test_deleted_manga_returns_empty(self):
        client = make_client({'manga/1--test/chapters': {'data': None}})
        assert run(client.get_chapters('1--test')) == []


class TestGetChapterPages:
    def test_urls_prefixed(self):
        client = make_client({
            'manga/1--test/chapter': {'data': {'pages': [{'url': '/a.jpg'}, {'url': '/b.jpg'}]}}
        })
        pages = run(client.get_chapter_pages('1--test', 1, '10.5'))
        assert pages == [f'{BASE_IMG_URL}/a.jpg', f'{BASE_IMG_URL}/b.jpg']
        # номера уходят в API строками
        _, params = client.calls[0]
        assert params == {'number': '10.5', 'volume': '1'}

    def test_no_pages(self):
        client = make_client({'manga/1--test/chapter': {'data': {'pages': None}}})
        assert run(client.get_chapter_pages('1--test', 1, 1)) == []


class TestMe:
    def test_unwraps_data(self):
        client = make_client({'auth/me': {'data': {'id': 7011590, 'username': 'damir'}}})
        assert run(client.me())['username'] == 'damir'

    def test_flat_response(self):
        client = make_client({'auth/me': {'id': 7011590, 'username': 'damir'}})
        assert run(client.me())['username'] == 'damir'


class TestToken:
    def test_has_token(self):
        assert MangaLibClient(token='abc').has_token

    def test_token_in_headers(self):
        client = MangaLibClient(token='abc')
        assert client.headers['Authorization'] == 'Bearer abc'
