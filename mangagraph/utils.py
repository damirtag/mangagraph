
import re, hashlib
from typing         import Union
from urllib.parse   import urlparse

from .exceptions    import InvalidURLException
from .constants     import CHAPTERS_PER_MINUTE

# Поддерживаемые форматы:
#   https://mangalib.me/ru/manga/7965--chainsaw-man
#   https://mangalib.me/ru/7965--chainsaw-man/read/v1/c1
#   https://mangalib.me/manga/7965--chainsaw-man (старый формат)
SLUG_PATTERN = re.compile(r'^/(?:ru/)?(?:manga/)?(\d+--[\w\-]+)')


def extract_slug(url: Union[str, object]) -> str:
    url = str(url)
    parsed = urlparse(url)

    if parsed.scheme != 'https' or parsed.netloc != 'mangalib.me':
        raise InvalidURLException(url, "Только 'https://mangalib.me' поддерживается.")

    match = SLUG_PATTERN.match(parsed.path)
    if not match:
        raise InvalidURLException(
            url,
            "Ссылка должна быть одного из типов:\n"
            "- 'https://mangalib.me/ru/manga/{slug_url}'\n"
            "- 'https://mangalib.me/ru/{slug_url}/read/v{volume}/c{chapter}'"
        )
    return match.group(1)


def normalize_chapter_number(value: Union[int, float, str, None]) -> str:
    """
    Приводит номер главы/тома к каноничной строке:
    10 -> '10', 10.0 -> '10', '10.50' -> '10.5', 'extra' -> 'extra'.

    MangaLib отдает номера строками, и главы вида '10.5' — обычное дело,
    поэтому хранить и сравнивать их можно только как строки.
    """
    if value is None:
        return ''
    text = str(value).strip()
    try:
        number = float(text)
    except ValueError:
        return text
    if number.is_integer():
        return str(int(number))
    return repr(number)


def estimate_remaining_time(
    remaining_chapters: int,
    chapters_per_minute: int = CHAPTERS_PER_MINUTE
) -> str:
    estimated_minutes = (remaining_chapters / chapters_per_minute) * 1.1

    if estimated_minutes < 1:
        return "меньше минуты"

    hours = int(estimated_minutes // 60)
    minutes = int(estimated_minutes % 60)

    if hours > 0:
        return f"{hours} ч {minutes} мин"
    return f"{minutes} мин"


def sanitize_db_name(db_name: str) -> str:
    clean_name = re.sub(r'[^\w\-.]', '_', db_name)

    if len(clean_name) < 3 or clean_name == '_' * len(clean_name):
        hash_suffix = hashlib.md5(db_name.encode()).hexdigest()[:8]
        safe_name = f"{hash_suffix}.db"
    else:
        safe_name = clean_name + '.db'
    return safe_name
