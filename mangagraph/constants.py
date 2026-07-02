import os

from pathlib import Path

MAX_CONCURRENT      = 3
CHAPTERS_PER_MINUTE = 12
BASE_IMG_URL        = "https://img2.imglib.info"
API_BASE_URL        = "https://api2.mangalib.me/api/"
TELEGRAPH_CREDS     = dict(
    short_name  ='Damir',
    author_name ='Создано mangagraph',
    author_url  ='https://github.com/damirTAG/mangagraph'
)

TOKEN_ENV_VAR       = 'MANGALIB_TOKEN'
DEFAULT_USER_AGENT  = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
)


def _load_dotenv(path: str = '.env'):
    """Минимальный загрузчик .env (KEY=VALUE), чтобы не тянуть python-dotenv."""
    env_file = Path(path)
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_headers(token: str = None) -> dict:
    """
    Собирает заголовки для запросов к API MangaLib.

    Токен берется из аргумента, переменной окружения MANGALIB_TOKEN
    или файла .env в текущей директории.
    Без токена запросы идут анонимно (поиск может быть недоступен).
    """
    headers = {'User-Agent': DEFAULT_USER_AGENT}
    if not token and TOKEN_ENV_VAR not in os.environ:
        _load_dotenv()
    token = token or os.environ.get(TOKEN_ENV_VAR)
    if token:
        if not token.startswith('Bearer '):
            token = f'Bearer {token}'
        headers['Authorization'] = token
    return headers
