# Mangagraph

#### From Mangalib to Telegraph with ❤️

[![PyPI](https://img.shields.io/pypi/v/mangagraph?logo=pypi&logoColor=white&color=blue)](https://pypi.org/project/mangagraph/)
[![Downloads](https://img.shields.io/pypi/dm/mangagraph?style=flat-square)](https://pypi.org/project/mangagraph/)
[![CI/CD](https://github.com/damirtag/mangagraph/actions/workflows/python-publish.yml/badge.svg)](https://github.com/damirtag/mangagraph/actions/workflows/python-publish.yml)
[![Telegram](https://img.shields.io/badge/Telegram-@damirtag-26A5E4?logo=telegram&logoColor=white)](https://t.me/damirtag)

Асинхронный парсер-конвертер манги из mangalib api в telegraph

## Принцип работы

Даем **ссылку на мангу**
**(такого типа: https://mangalib.me/ru/manga/{slug_url}) и название бд**
куда мы сохраняем _(том, главу, наименование главы, ссылку на главу для чтения и зеркало на случаи_
_если главная ссылка не доступна)_ -> получаем полные данные о главах -> генерируем телеграф страницы
на каждую главу -> ссылки на страницу сохраняем в `SQLite` бд, с использованием `SQLAlchemy`

**-> На выходе**
получаем базу данных готовую к любому использованию и конечную ссылку телеграфа с зеркалом (оглавление) внутри
которой находятся все главы с именами и ссылкой для чтения

Пример страницы главы: https://telegra.ph/Vanpanchmen--VanPanchMen-vyhodit-na-scenu-07-02

Пример оглавления: https://graph.org/Vanpanchmen-01-22-3 (ссылки на оглавление также сохраняются в бд, в таблицу ToC_url)

## Установка

```bash
pip install -U mangagraph
```

## Токен MangaLib

Для поиска манги нужен персональный Bearer-токен MangaLib
(как его получить — см. [.env.example](.env.example)).
Задайте его через переменную окружения:

```bash
export MANGALIB_TOKEN="eyJ0eXAiOiJKV1QiLCJh..."
```

либо положите в файл `.env` в рабочей директории (см. `.env.example`),
либо передайте напрямую в коде: `Mangagraph(token="...")`.
Обработка глав по прямой ссылке работает и без токена.

## Использование

#### CLI

```bash
mangagraph --url https://mangalib.me/ru/manga/706--onepunchman
```

или

```bash
python -m mangagraph --url https://mangalib.me/ru/manga/706--onepunchman
```

Обработка одной конкретной главы (к примеру вторая)

> Важно! При обработки одной главы не создается БД и оглавление, возвращается только кортеж из двух строк (главной ссылки и зеркала)

```bash
mangagraph --url https://mangalib.me/ru/manga/706--onepunchman --c 2
```

Несколько глав, диапазоны и половинные главы:

```bash
mangagraph --url https://mangalib.me/ru/manga/706--onepunchman --c "1,2,5,10"
mangagraph --url https://mangalib.me/ru/manga/706--onepunchman --c "1-10"
mangagraph --url https://mangalib.me/ru/manga/706--onepunchman --c "1,5-10,20.5"
```

#### Поиск манги

```bash
mangagraph --q "Berserk" --limit 10
```

#### Raw

```py
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
        for num, (toc, mirror) in results.items():
            print(f"Глава №{num}")
            print(f"   TOC: {toc}")
            print(f"   Mirror: {mirror}\n")

        # Парсинг манги и загрузка телеграф
        result = await mgraph.process_manga('https://mangalib.me/ru/manga/706--onepunchman')

        if result:
            toc_url, mirror_toc_url = result
            print(f"Table of Contents: {toc_url}")
            print(f"Mirror: {mirror_toc_url}")
    except MangagraphError as e:
        print(f"Parser error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

import asyncio

asyncio.run(main())
```

#### Прямой доступ к API MangaLib

Все запросы к API живут в `MangaLibClient` — его можно использовать отдельно,
без Telegraph и базы данных (также доступен как `mgraph.client`):

```py
from mangagraph import MangaLibClient

async with MangaLibClient() as client:   # токен из MANGALIB_TOKEN / .env
    me = await client.me()               # данные текущего пользователя
    results = await client.search("Berserk", limit=3)
    chapters = await client.get_chapters("7965--chainsaw-man")
    pages = await client.get_chapter_pages("7965--chainsaw-man", volume=1, chapter=1)
```

Новые методы API добавляются в `MangaLibClient` — один метод на endpoint.

## Разработка

```bash
git clone https://github.com/damirTAG/mangagraph
cd mangagraph
pip install -e ".[dev]"
pytest
```