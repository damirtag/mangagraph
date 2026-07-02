import asyncio
import aiohttp

from typing         import List, Dict, Any, Optional, Union

from .schemas       import SearchData
from .exceptions    import RequestFailedException
from .utils         import normalize_chapter_number
from .constants     import (
    MAX_CONCURRENT,
    API_BASE_URL,
    BASE_IMG_URL,
    get_headers
)

ChapterNumber = Union[int, float, str]


class MangaLibClient:
    """
    HTTP-клиент для API MangaLib. Только запросы к API — без Telegraph и БД.

    Можно использовать самостоятельно:

        async with MangaLibClient() as client:
            results = await client.search("Berserk")
            chapters = await client.get_chapters("7965--chainsaw-man")

    Либо без контекстного менеджера — сессия создается лениво,
    закрывается через `await client.close()`.

    Args:
        token: Персональный Bearer-токен MangaLib (нужен для поиска и auth-методов).
            Если не передан — берется из MANGALIB_TOKEN (env или .env).
        max_concurrent: Максимум одновременных запросов к API.
    """
    def __init__(self, token: Optional[str] = None, max_concurrent: int = MAX_CONCURRENT):
        self.headers    = get_headers(token)
        self.semaphore  = asyncio.Semaphore(max_concurrent)
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def has_token(self) -> bool:
        return 'Authorization' in self.headers

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session is not None and not self._session.closed:
            await self._session.close()
        self._session = None

    async def __aenter__(self) -> 'MangaLibClient':
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def _request(self, endpoint: str, params: Dict = None) -> Dict:
        """GET-запрос к API с ретраями и экспоненциальным backoff."""
        url = f"{API_BASE_URL}{endpoint}"
        session = await self._ensure_session()
        async with self.semaphore:
            for attempt in range(3):
                try:
                    async with session.get(url, params=params, headers=self.headers) as response:
                        response.raise_for_status()
                        return await response.json()
                except Exception as e:
                    if attempt == 2:
                        raise RequestFailedException(url, str(e))
                    await asyncio.sleep(2 ** attempt)

    # --- Манга ---

    async def get_manga(self, slug: str) -> Dict[str, Any]:
        """Полные данные манги по slug (например '7965--chainsaw-man')."""
        data = await self._request(f"manga/{slug}")
        return (data or {}).get('data') or {}

    async def get_manga_name(self, slug: str) -> str:
        manga = await self.get_manga(slug)
        return manga.get('rus_name') or manga.get('name') or 'Unknown'

    async def get_chapters(
        self, slug: str, chapter_num: Optional[ChapterNumber] = None
    ) -> List[Dict[str, Any]]:
        """
        Список глав манги. Может быть пустым — главы иногда удаляются
        по требованиям copyright.

        Args:
            chapter_num: Если передан — вернуть только главы с этим номером
                (поддерживаются половинные: 10.5, "10.5").
        """
        data = await self._request(f"manga/{slug}/chapters")

        if not data or not isinstance(data.get('data'), list):
            return []

        chapters = data['data']

        if chapter_num is not None:
            wanted = normalize_chapter_number(chapter_num)
            chapters = [
                chapter for chapter in chapters
                if normalize_chapter_number(chapter.get("number")) == wanted
            ]

        return chapters

    async def get_chapter_pages(
        self, slug: str, volume: ChapterNumber, chapter: ChapterNumber
    ) -> List[str]:
        """Полные URL страниц (изображений) главы."""
        params = {'number': str(chapter), 'volume': str(volume)}
        data = await self._request(f"manga/{slug}/chapter", params)
        pages = (data or {}).get('data', {}).get('pages') or []
        return [f"{BASE_IMG_URL}{page['url']}" for page in pages]

    async def search(self, query: str, limit: int = 5) -> List[SearchData]:
        """Поиск манги по названию. Требует токен."""
        params = {
            "fields[]": ["rate_avg", "rate", "releaseDate"],
            "q": query,
            "site_id[]": [1]
        }
        data = await self._request("manga", params)
        return [
            SearchData.de_json(manga_data)
            for manga_data in (data or {}).get('data', [])[:limit]
        ]

    # --- Аккаунт (требуют токен) ---
    # Новые методы API добавляются сюда: один метод — один endpoint,
    # ~5 строк делегирования в self._request.

    async def me(self) -> Dict[str, Any]:
        """Данные текущего пользователя по токену."""
        data = await self._request("auth/me")
        return (data or {}).get('data') or data or {}
