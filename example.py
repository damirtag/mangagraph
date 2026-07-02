import asyncio

from mangagraph import Mangagraph, MangaLibClient
from mangagraph.exceptions import MangagraphError

async def main():
    try:
        # Токен MangaLib (нужен для поиска) можно передать напрямую
        # или через переменную окружения MANGALIB_TOKEN / файл .env
        mgraph = Mangagraph()

        # Прямой доступ к API MangaLib — без Telegraph и БД
        async with MangaLibClient() as client:
            if client.has_token:
                me = await client.me()
                print(f"Авторизован как: {me.get('username')} (id={me.get('id')})")

            chapters = await client.get_chapters('7965--chainsaw-man')
            print(f"Глав у Бензочела: {len(chapters)}\n")

        # Поиск манги по ключевому слову и с лимитом
        results = await mgraph.search_manga("Berserk", limit=3)

        for idx, result in enumerate(results, 1):
            print(f"{idx}. {result.name} / {result.rus_name}")
            print(f"   Рейтинг: {result.rating.raw_average} ({result.rating.raw_votes} отзывов)")
            print(f"   Год: {result.release_year} | Тип: {result.type} | Статус: {result.status}")
            print(f"   Ссылка: https://mangalib.me/ru/manga/{result.slug_url}")
            print()

        # Парсинг одной конкретной главы (поддерживаются и половинные: "97.5")
        chapter_num = 97
        result = await mgraph.process_chapters(
            'https://mangalib.me/ru/manga/7965--chainsaw-man',
            chapter_num
        )
        if result:
            url, mirror_url = result
            print(f'Бензочел, глава номер {chapter_num}: {url} | {mirror_url}')

        # Парсинг нескольких глав сразу
        results = await mgraph.process_chapters(
            'https://mangalib.me/ru/manga/7965--chainsaw-man',
            chapter_nums=[90, 91, 92]
        )

        print("Главы:\n")
        for num, links in results.items():
            if links is None:
                print(f"Глава №{num}: не обработана\n")
                continue
            toc, mirror = links
            print(f"Глава №{num}")
            print(f"   TOC: {toc}")
            print(f"   Mirror: {mirror}\n")

        # Парсинг манги целиком и загрузка в телеграф
        result = await mgraph.process_manga('https://mangalib.me/ru/manga/706--onepunchman')

        if result:
            toc_url, mirror_toc_url = result
            print(f"Table of Contents: {toc_url}")
            print(f"Mirror: {mirror_toc_url}")
    except MangagraphError as e:
        print(f"Parser error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

asyncio.run(main())
