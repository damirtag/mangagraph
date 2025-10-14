from mangagraph import Mangagraph
from mangagraph.exceptions import MangagraphError

async def main():
    try:
        mgraph = Mangagraph()
        # Поиск манги по ключевому слову и с лимитом
        results = await mgraph.search_manga("Berserk", limit=3)

        for idx, result in enumerate(results, 1):
            print(f"{idx}. {result.name} / {result.rus_name}")
            print(f"   Рейтинг: {result.rating.raw_average} ({result.rating.raw_votes} отзывов)")
            print(f"   Год: {result.release_year} | Тип: {result.type} | Статус: {result.status}")
            print(f"   Ссылка: https://mangalib.me/ru/manga/{result.slug_url}")
            print()

        # Парсинг одной конкретной главы
        chapter_num = 97
        url, mirror_url = await mgraph.process_chapter(
            'https://mangalib.me/ru/manga/7965--chainsaw-man',
            chapter_num
        )
        print(f'Бензочел, глава номер {chapter_num}: {url} | {mirror_url}')

        # Парсинг нескольких глав сразу
        results = await mgraph.process_chapters(
            'https://mangalib.me/ru/manga/7965--chainsaw-man',
            chapter_nums=[90, 91, 92]
        )

        print("Главы:\n")
        for num, (toc, mirror) in results.items():
            print(f"📖 Глава №{num}")
            print(f"   TOC: {toc}")
            print(f"   Mirror: {mirror}\n")

        # Парсинг манги и загрузка телеграф
        toc_url, mirror_toc_url = await mgraph.process_manga('https://mangalib.me/ru/manga/706--onepunchman')

        print(f"Table of Contents: {toc_url}")
        print(f"Mirror: {mirror_toc_url}")
    except MangagraphError as e:
        print(f"Parser error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

import asyncio

asyncio.run(main())