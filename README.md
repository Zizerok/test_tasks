# Тестовое задание QA

## Структура

- `docs/` — чек-лист, детальные тест-кейсы и баг-репорты.
- `backend/` — проверяемое приложение FastAPI и зависимости.
- `backend_tests/` — Python-тесты, фикстуры и схема PostgreSQL.
- `cpp_tests/cpp-spreadsheet/` — исходники Spreadsheet и C++-тесты.
- `scripts/` — подготовка тестовой БД.
- `.github/workflows/` — автоматические проверки GitHub Actions.

## Тесты

- **Python** — `test_api.py` проверяет API и валидацию, `test_db_workflow.py` — изменения в PostgreSQL, `test_concurrency.py` — два отклика на последнее место. Фикстуры находятся в `conftest.py`. Исходящий VK API подменён моком, приложение и PostgreSQL настоящие.
- **C++** — в `cpp_tests/cpp-spreadsheet/spreadsheet/main.cpp` добавлены `TestClearCellInvalidatesDependentCache`, `TestReferencedEmptyCellDoesNotIncreasePrintableSize` и `TestClearCellRemovesReverseDependency`.
- **CI** — `.github/workflows/tests.yml` запускает Ruff и pytest при push и pull request.

Четыре расхождения валидации описаны в [bug_reports.md](docs/bug_reports.md).

## Просмотр результатов в GitHub Actions

Python-проверки можно посмотреть без локальной установки: открыть вкладку Actions, выбрать workflow Python checks и нужный запуск.

Проверки запускаются при push и pull request. При наличии прав записи повторный запуск доступен через **Run workflow**. C++-тесты этим workflow не запускаются. Команды ниже нужны только для локального запуска.

## Запуск Python-тестов
Команды — для Windows cmd из корня репозитория.

python -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements-test.txt
copy backend\.env.test.example backend\.env.test


В `backend/.env.test` указать пароль локального PostgreSQL для пользователя `postgres`. Имя БД оставить `vkr_test`; при необходимости изменить адрес, порт и `POSTGRES_BIN_PATH`. Уже настроенный файл не перезаписывать.

backend\.venv\Scripts\python.exe scripts\prepare_test_db.py
backend\.venv\Scripts\python.exe -m pytest backend_tests -v


## Проверка линтером

backend\.venv\Scripts\python.exe -m pip install ruff==0.17.0
backend\.venv\Scripts\python.exe -m ruff check backend backend_tests scripts
backend\.venv\Scripts\python.exe -m ruff format --check backend backend_tests scripts

