import argparse
import asyncio
import logging

from .parser        import Mangagraph
from .exceptions    import MangagraphError

mgraph = Mangagraph()

async def search_manga(query: str, limit: int = 5):
    results = await mgraph.search_manga(query, limit=limit)
    
    if not results:
        print("Не найдено подходящих манг по запросу.")
        return None

    print(f"\nНайдено {len(results)} по запросу '{query}':")
    for idx, result in enumerate(results, 1):
        print(f"\n{idx}. {result.name} / {result.rus_name}")
        print(f"   Рейтинг: {result.rating.raw_average}/10 ({result.rating.raw_votes} оценок)")
        print(f"   Год: {result.release_year} | Тип: {result.type} | Статус: {result.status}")
        print(f"   Возраст: {result.age_restriction}")

    try:
        choice = int(input(f"\nВыберите мангу (1-{len(results)}, 0 - для отмены): "))
        if choice == 0:
            return None
        if 1 <= choice <= len(results):
            return results[choice-1].slug_url
        else:
            print("Неверный номер.")
            return None
    except ValueError:
        print("Неверный запрос.")
        return None

def parse_chapter_input(chapter_str: str) -> list:
    """
    Parse chapter input string into list of chapter numbers.
    
    Supports formats:
    - Single: "42" -> [42]
    - Comma-separated: "1,2,3" -> [1, 2, 3]
    - Range: "1-5" -> [1, 2, 3, 4, 5]
    - Mixed: "1,3,5-7,10" -> [1, 3, 5, 6, 7, 10]
    """
    chapters = []
    parts = chapter_str.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            # Handle range
            try:
                start, end = part.split('-')
                start, end = int(start.strip()), int(end.strip())
                chapters.extend(range(start, end + 1))
            except ValueError:
                raise ValueError(f"Неверный формат диапазона: {part}")
        else:
            # Handle single number
            try:
                chapters.append(int(part))
            except ValueError:
                raise ValueError(f"Неверный номер главы: {part}")
    
    return sorted(list(set(chapters)))  # Remove duplicates and sort

async def main():
    parser = argparse.ArgumentParser(
        description="Mangagraph - Manga to Telegraph converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Обработка всей манги
  mangagraph --url https://mangalib.me/one-piece
  
  # Поиск манги
  mangagraph --q "one piece"
  
  # Обработка одной главы
  mangagraph --url https://mangalib.me/one-piece --c 1050
  
  # Обработка нескольких глав
  mangagraph --url https://mangalib.me/one-piece --c "1,2,3"
  
  # Обработка диапазона глав
  mangagraph --url https://mangalib.me/one-piece --c "1-10"
  
  # Смешанный формат
  mangagraph --url https://mangalib.me/one-piece --c "1,5,10-15,20"
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--url', type=str, help='URL манги для обработки')
    group.add_argument('--q', type=str, help='Поиск манги по названию')

    parser.add_argument('--db', type=str, help='Имя БД (по умолчанию - название манги)')
    parser.add_argument(
        '--c', 
        type=str, 
        help='Номер главы(глав) для обработки. Форматы: "42", "1,2,3", "1-10", "1,5-10,15"'
    )
    parser.add_argument(
        '--limit', 
        type=int, 
        default=5, 
        help='Максимальное количество результатов поиска (по умолчанию 5)'
    )
    parser.add_argument(
        '--concurrent',
        type=int,
        default=3,
        help='Количество одновременно обрабатываемых глав (по умолчанию 3)'
    )
    
    args = parser.parse_args()
    logger = logging.getLogger(__name__)
    
    try:
        if args.q:
            logger.info(f"Поиск: {args.q}")
            slug = await search_manga(args.q, args.limit)
            
            if not slug:
                logger.info("Поиск отменен или ни одна из манг не выбрана.")
                return
                
            logger.info(f"Выбрана манга: {slug}")
            manga_url = f"https://mangalib.me/ru/manga/{slug}"
        else:
            manga_url = args.url

        # Process specific chapters
        if args.c:
            try:
                chapter_nums = parse_chapter_input(args.c)
            except ValueError as e:
                logger.error(f"Ошибка парсинга номеров глав: {e}")
                return
            
            if len(chapter_nums) == 1:
                # Single chapter
                logger.info(f'Обработка главы {chapter_nums[0]} | {manga_url}')
                result = await mgraph.process_chapters(manga_url, chapter_nums[0])
                
                if result:
                    url, mirror_url = result
                    logger.info(f"Ссылка: {url}")
                    logger.info(f"Зеркало: {mirror_url}")
                else:
                    logger.error(f"Не удалось обработать главу {chapter_nums[0]}")
            else:
                # Multiple chapters
                logger.info(
                    f'Обработка глав {chapter_nums} | {manga_url} '
                    f'(параллельность: {args.concurrent})'
                )
                results = await mgraph.process_chapters(
                    manga_url, 
                    chapter_nums,
                    max_concurrent=args.concurrent
                )
                
                # Display results
                successful = 0
                failed = 0
                
                print("\n" + "="*60)
                print("РЕЗУЛЬТАТЫ ОБРАБОТКИ")
                print("="*60)
                
                for chapter_num in chapter_nums:
                    result = results.get(chapter_num)
                    if result:
                        url, mirror_url = result
                        successful += 1
                        print(f"\n✓ Глава {chapter_num}:")
                        print(f"  Ссылка: {url}")
                        print(f"  Зеркало: {mirror_url}")
                    else:
                        failed += 1
                        print(f"\n✗ Глава {chapter_num}: Ошибка обработки")
                
                print("\n" + "="*60)
                print(f"Успешно: {successful}/{len(chapter_nums)}")
                if failed > 0:
                    print(f"Ошибок: {failed}/{len(chapter_nums)}")
                print("="*60)
            
            return

        # Process entire manga
        logger.info(f"Обработка манги: {manga_url}")
        toc_url, mirror_toc_url = await mgraph.process_manga(manga_url, args.db)
        
        logger.info(f"База данных создана!")
        logger.info(f"Оглавление: {toc_url}")
        logger.info(f"Зеркало оглавления: {mirror_toc_url}")
        
    except MangagraphError as e:
        logger.error(f"Parser error: {e}")
    except KeyboardInterrupt:
        logger.info("Operation canceled by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())