import asyncio
import json

import pytest

import mangagraph.telegraph as telegraph_module

from mangagraph.telegraph import TelegraphClient
from mangagraph.exceptions import TelegraphError


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    async def json(self):
        return self._payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeSession:
    """Отдает заготовленные ответы по очереди, запоминая запросы."""

    closed = False

    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.calls = []

    def post(self, url, data=None):
        self.calls.append((url, data))
        return FakeResponse(self.payloads.pop(0))


def make_client(payloads):
    client = TelegraphClient()
    client._session = FakeSession(payloads)
    return client


def run(coro):
    return asyncio.run(coro)


class TestRequest:
    def test_ok_returns_result(self):
        client = make_client([{'ok': True, 'result': {'path': 'x'}}])
        assert run(client._request('createPage')) == {'path': 'x'}

    def test_api_error_raises(self):
        client = make_client([{'ok': False, 'error': 'PAGE_NOT_FOUND'}])
        with pytest.raises(TelegraphError, match='PAGE_NOT_FOUND'):
            run(client._request('editPage'))

    def test_flood_wait_retries(self, monkeypatch):
        sleeps = []

        async def fake_sleep(seconds):
            sleeps.append(seconds)

        monkeypatch.setattr(telegraph_module.asyncio, 'sleep', fake_sleep)

        client = make_client([
            {'ok': False, 'error': 'FLOOD_WAIT_7'},
            {'ok': True, 'result': {'path': 'x'}},
        ])
        assert run(client._request('createPage')) == {'path': 'x'}
        assert sleeps == [7]
        assert client.flood_wait_count == 1

    def test_flood_wait_exhausts_retries(self, monkeypatch):
        async def fake_sleep(seconds):
            pass

        monkeypatch.setattr(telegraph_module.asyncio, 'sleep', fake_sleep)

        client = make_client([{'ok': False, 'error': 'FLOOD_WAIT_1'}] * 3)
        with pytest.raises(TelegraphError, match='flood wait'):
            run(client._request('createPage'))

    def test_none_params_dropped(self):
        client = make_client([{'ok': True, 'result': {}}])
        run(client._request('createAccount', short_name='D', author_url=None))
        _, data = client._session.calls[0]
        assert data == {'short_name': 'D'}


class TestMethods:
    def test_create_account_stores_token(self):
        client = make_client([{'ok': True, 'result': {'access_token': 'secret'}}])
        run(client.create_account(short_name='Damir'))
        assert client.access_token == 'secret'

    def test_create_page_serializes_content(self):
        client = make_client([{'ok': True, 'result': {'path': 'p', 'url': 'u'}}])
        client.access_token = 'token'
        content = [{'tag': 'img', 'attrs': {'src': 'https://img/1.jpg'}}]

        run(client.create_page(title='Т', content=content))

        url, data = client._session.calls[0]
        assert url.endswith('/createPage')
        assert data['access_token'] == 'token'
        assert json.loads(data['content']) == content

    def test_edit_page_sends_path(self):
        client = make_client([{'ok': True, 'result': {}}])
        client.access_token = 'token'
        run(client.edit_page(path='some-path', title='Т', content=[]))
        _, data = client._session.calls[0]
        assert data['path'] == 'some-path'
