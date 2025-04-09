"""
Author: https://github.com/damirtag | https://t.me/damirtag
GH Repo: https://github.com/damirtag/mangagraph

MIT License

Copyright (c) 2025 Tagilbayev Damir

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import asyncio
import aiohttp
import logging

from typing         import List, Dict, Any, Tuple, Optional

from sqlalchemy     import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .models        import Base, Chapter, TocURL
from .schemas       import SearchData
from .exceptions    import (
    MangagraphError,
    RequestFailedException
)
from .utils         import (
    MangaLibUrl, 
    estimate_remaining_time, 
    extract_slug,
    sanitize_db_name
)
from .constants     import (
    TELEGRAPH_CREDS,
    MAX_CONCURRENT,
    API_BASE_URL,
    BASE_IMG_URL,
    HEADERS
)

from telegraph.aio import Telegraph
from telegraph.exceptions import RetryAfterError

class Mangagraph():
    """
    Автор: https://github.com/damirtag

    Репозитории: https://github.com/damirTAG/mangagraph
    """
    def __init__(self):
        self.logger     = self._setup_logger()
        self.telegraph  = Telegraph()
        self.semaphore  = asyncio.Semaphore(MAX_CONCURRENT)

        self.processed_count    = 0
        self.total_chapters     = 0
        self.flood_wait_count   = 0

        self.headers = HEADERS

    def _setup_logger(self):
        logger = logging.getLogger('mangagraph')
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[mangagraph]: %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        if not logger.handlers:
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def _setup_db(self, db_name: str) -> Session:
        try:
            db_name = sanitize_db_name(db_name)
            self.logger.info(f'Имя БД: {db_name}')

            engine = create_engine(f'sqlite:///{db_name}')
            Base.metadata.create_all(engine)

            SessionLocal = sessionmaker(bind=engine)

            return SessionLocal()
        except Exception as e:
            self.logger.error(f'Error trying to setup database: {e}')
            return None

    async def _make_request(
            self, session: aiohttp.ClientSession, url: str, params: Dict = None
        ) -> Dict:
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

    async def _get_manga_name(self, session: aiohttp.ClientSession, slug: str) -> tuple[str, str]:
        url = f"{API_BASE_URL}manga/{slug}"
        data: dict = await self._make_request(session, url)
        
        manga_name = data.get('data', {}).get('rus_name', 1)
        if manga_name == 1:
            manga_name = data.get('data', {}).get('name', 'Unknown')
        
        return manga_name

    async def get_chapters_info(
            self, session: aiohttp.ClientSession, slug: str, chapter_num: Optional[float] = None
        ) -> List[Dict[str, Any]]:
        url = f"{API_BASE_URL}manga/{slug}/chapters"
        data = await self._make_request(session, url)

        if not data or 'data' not in data or not isinstance(data['data'], list):
            self.logger.error(f"Похоже, главы в манге были удалены: {slug}")
            return []  # Некоторые манги могут быть с пустыми главами 
            # из-за удаления по требованиям copyright

        chapters = data['data']

        # Фильтруем по номеру главы, если параметр передан
        if chapter_num is not None:
            chapters = [chapter for chapter in chapters if float(chapter.get("number", 0)) == chapter_num]

        return chapters

    async def get_chapter_pages(
        self, 
        session: aiohttp.ClientSession, 
        slug: str, 
        volume: int, 
        chapter: int
    ) -> List[str]:
        url = f"{API_BASE_URL}manga/{slug}/chapter"
        params = {'number': chapter, 'volume': volume}
        data = await self._make_request(session, url, params)
        return [f"{BASE_IMG_URL}{page['url']}" for page in data['data']['pages']]

    async def search_manga(
            self, query: str, limit: int = 5
        ) -> list[SearchData]:
        url = f"{API_BASE_URL}manga"
        params = {
            "fields[]": ["rate_avg", "rate", "releaseDate"],
            "q": query,
            "site_id[]": [1]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=self.headers) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    results = []
                    for manga_data in data.get('data', [])[:limit]:
                        search_data = SearchData.de_json(manga_data)
                        results.append(search_data)
                    
                    return results
        except aiohttp.ClientError as e:
            print(f"Error during search request: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error during search: {e}")
            return []

    async def _create_telegraph_page(
            self, 
            title: str, 
            image_urls: List[str],
            retry_count: int = 3
        ) -> Tuple[str, str]:
        html_content = "".join(f'<img src="{url}"/>\n' for url in image_urls)
        
        for attempt in range(retry_count):
            try:
                response = await self.telegraph.create_page(
                    title=title,
                    html_content=html_content,
                    author_name='Auto-Generated by MGLParser',
                    author_url='https://github.com/damirTAG/mangagraph'
                )
                
                return (
                    f"https://telegra.ph/{response['path']}", 
                    f"https://graph.org/{response['path']}"
                )
            except RetryAfterError:
                self.flood_wait_count += 1
                wait_time = 7
                            
                self.logger.info(
                    f'Flood wait #{self.flood_wait_count} detected, ' 
                    f'waiting {wait_time} seconds. ' 
                    f'Total floods: {self.flood_wait_count}'
                )
                    
                await asyncio.sleep(wait_time)
                await self.telegraph.create_account(
                    **TELEGRAPH_CREDS
                )
                continue
            except Exception as e:
                raise MangagraphError(f"Не удалось создать telegraph страницу: {str(e)}")

    async def _construct_chapters_list(
        self, 
        title: str, 
        chapters: List[Tuple[int, int, str, str, str]]
    ) -> str:
        """Creates a table of contents page in Telegraph."""
        content = [
            {
                "tag": "p",
                "children": ["Создано Mangagraph, developer - ", {
                    "tag": "a", 
                    "attrs": {"href": "https://t.me/damirtag"}, 
                    "children": ["@damirtag"]}
                ]
            }
        ]
        
        for volume, chapter_num, chapter_title, url, mirror_url in chapters:
            content.append({
                "tag": "p",
                "children": [
                    {
                        "tag": "a",
                        "attrs": {"href": mirror_url},
                        "children": [f"Volume {volume} Chapter {chapter_num}: {chapter_title}"]
                    }
                ]
            })

        try:
            response = await self.telegraph.create_page(
                title=title,
                author_name='Damir',
                author_url='https://github.com/damirtag/mangagraph',
                content=content
            )
            toc_url = response['url']
            mirror_toc_url = toc_url.replace("telegra.ph", "graph.org")

            return toc_url, mirror_toc_url
        except Exception as e:
            raise MangagraphError(f'Telegraph says: {str(e)}')

    async def process_manga(self, manga_url: MangaLibUrl, db_name: str = None):
        """
        Параметры:
            manga_url (str): URL манги, которую нужно обработать.
            db_name (str): Название файла базы данных, по дефолту дается по имени манги

        Возвращает:

            Кортеж из двух строк:

                - URL оглавления в Telegraph.

                - URL зеркала оглавления в graph.org (если используется).

        Исключения:
            MangagraphError: Выбрасывается, если возникает ошибка при обработке манги.
            InvalidURLException: Выбрасывается, если URL манги недействителен.
            RequestFailedException: Выбрасывается, если запрос к API завершается неудачей.
        """
        await self.telegraph.create_account(
            **TELEGRAPH_CREDS
        )
        slug = extract_slug(manga_url)
        
        async with aiohttp.ClientSession() as session:
            try:
                manga_name  = await self._get_manga_name(session, slug)
                chapters    = await self.get_chapters_info(session, slug)
                if not chapters:
                    self.logger.error(f"Похоже, главы в манге были удалены: https://mangalib.me/ru/{slug}")
                    return
                
                db_session: Session  = self._setup_db(
                    manga_name if not db_name else db_name
                )
                if db_session is None:
                    raise RuntimeError("Не удалось создать сессию базы данных.")
                
                self.total_chapters = len(chapters)
                self.processed_count = 0
                processed_chapters = []

                first_chapter = chapters[0]
                pages = await self.get_chapter_pages(
                    session,
                    slug,
                    first_chapter.get('volume'),
                    first_chapter.get('number')
                )
                
                for chapter_info in chapters:
                    volume = chapter_info.get('volume')
                    chapter_num = chapter_info.get('number')
                    title = (
                        f"{manga_name} | {chapter_info.get('name', f'Том {volume}, Глава {chapter_num}')}" 
                    )

                    existing_chapter = db_session.query(Chapter).filter_by(
                        volume=volume, 
                        chapter=chapter_num
                    ).first()

                    if existing_chapter:
                        self.processed_count += 1
                        processed_chapters.append(
                            (volume, chapter_num, title, existing_chapter.url, existing_chapter.mirror_url)
                        )
                        remaining = self.total_chapters - self.processed_count
                        est_time = estimate_remaining_time(remaining)
                        self.logger.info(
                            f"Глава {chapter_num} уже существует, пропускаем... " 
                            f"[{self.processed_count}/{self.total_chapters}] " 
                            f"Примерное время: {est_time}"
                        )
                        continue

                    try:
                        pages = await self.get_chapter_pages(
                            session,
                            slug, 
                            volume, 
                            chapter_num
                        )
                        
                        url, mirror_url = await self._create_telegraph_page(
                            title=title,
                            image_urls=pages
                        )
                        
                        new_chapter = Chapter(
                            volume=volume,
                            chapter=chapter_num,
                            title=title,
                            url=url,
                            mirror_url=mirror_url
                        )
                        db_session.add(new_chapter)
                        db_session.commit()
                        
                        self.processed_count += 1
                        processed_chapters.append((volume, chapter_num, title, url, mirror_url))
                        
                        remaining = self.total_chapters - self.processed_count
                        est_time = estimate_remaining_time(remaining)
                        self.logger.info(
                            f"Обработана глава: {title} " 
                            f"[{self.processed_count}/{self.total_chapters}] " 
                            f"Осталось: {est_time}"
                        )
                        
                        await asyncio.sleep(3)
                        
                    except Exception as e:
                        self.logger.error(
                            f"Ошибка обработки главы {chapter_num}: {str(e)}\n" 
                            f"Всего обработано: {self.processed_count}/{self.total_chapters}"
                        )
                        db_session.rollback()
                        break

                if processed_chapters:
                    toc_url, mirror_toc_url = await self._construct_chapters_list(
                        manga_name,
                        processed_chapters
                    )
                    toc_db = TocURL(
                        manga_name=manga_name,
                        url=toc_url,
                        mirror_url=mirror_toc_url
                    )
                    db_session.add(toc_db)
                    db_session.commit()

                    self.logger.info(f"Создано оглавление: {toc_url}")
                    self.logger.info(f"Всего обработано: {self.processed_count}/{self.total_chapters}")
                    self.logger.info(f"Зеркало: {mirror_toc_url}")

                    return toc_url, mirror_toc_url

            except (KeyboardInterrupt, SystemExit):
                self.logger.info('Sayonara!')

            finally:
                db_session.close()

    async def process_chapter(
            self, manga_url: MangaLibUrl, chapter_num: int
        ) -> Tuple[str, str]:
        """
        Обработка одной главы манги.

        Параметры:
            manga_url (str): URL манги на MangaLib.
            chapter_num (int): Номер главы, которую нужно обработать.

        Возвращает:
            Tuple[str, str] | None: URL страницы Telegraph и ее зеркало, если обработка успешна, иначе None.
        """
        await self.telegraph.create_account(
            **TELEGRAPH_CREDS
        )
        slug = extract_slug(manga_url)

        async with aiohttp.ClientSession() as session:
            try:
                manga_name          = await self._get_manga_name(session, slug)
                chapter_list        = await self.get_chapters_info(session, slug, chapter_num)
                if not chapter_list:
                    raise MangagraphError(f"Похоже, главы в манге были удалены: https://mangalib.me/ru/{slug}")
                chapter = chapter_list[0]

                pages = await self.get_chapter_pages(
                    session,
                    slug,
                    chapter.get('volume'),
                    chapter.get('number')
                )
                if not pages:
                    raise MangagraphError(f"Не удалось получить страницы манги: https://mangalib.me/ru/{slug}")

                volume = chapter.get('volume')
                chapter_num = chapter.get('number')
                title = (
                    f"{manga_name} | {chapter.get('name', f'Том {volume}, Глава {chapter_num}')}" 
                )

                try:
                    url, mirror_url = await self._create_telegraph_page(
                        title=title,
                        image_urls=pages
                    )
                    self.logger.info(f"Обработана глава: {title}")
                    return url, mirror_url
                except Exception as e:
                    self.logger.error(f"Ошибка обработки главы {chapter_num}: {str(e)}\n")
                    return None

            except Exception as e:
                self.logger.error(f'Ошибка при обработке главы: {e}')
