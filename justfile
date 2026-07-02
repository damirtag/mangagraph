# Список команд
default:
    @just --list

# Установка в dev-режиме со всеми зависимостями
install:
    pip install -e ".[dev]"

# Запуск тестов
test:
    pytest

# Прогон примера
example:
    python example.py

# Очистка артефактов сборки
clean:
    rm -rf dist build *.egg-info

# Сборка sdist + wheel
build: clean
    python -m build

# Проверка собранного пакета перед публикацией
check: build
    twine check dist/*

# Ручная публикация в PyPI (обычно не нужна — релиз идет через тег и GitHub Actions)
# publish: check
#     twine upload dist/*
