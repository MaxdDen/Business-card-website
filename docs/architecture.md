## Этап 0 — базовая архитектура и окружение

- Ядро: FastAPI (`app/main.py`) с healthcheck `GET /health`.
- Структура каталогов: `app/{auth,cms,site,static,templates,utils,database}`.
- Конфигурация окружения: `.env` (пример в `.env.example`), загрузка через `python-dotenv`.
- Стили: TailwindCSS, вход `app/static/css/input.css`, выход `app/static/css/output.css`; конфиг `tailwind.config.js`, скрипты в `package.json`.
- Зависимости Python: перечислены в `requirements.txt` (FastAPI, Uvicorn, Jinja2, python-multipart, passlib[bcrypt], PyJWT, Pillow, python-dotenv, email-validator).
- Базовые правила репозитория: `.gitignore`, `.editorconfig`.

Решения:
- Минимальный HTTP‑интерфейс для проверки живости сервиса без БД.
- Tailwind внедряется на уровне сборки, без фреймворков UI.
- Мультиязычность будет реализована далее, но языки по умолчанию заданы через `.env`.

## Этап 1 — база данных и слой доступа (без ORM)

- Хранилище: SQLite в `data/app.db`, включён `PRAGMA foreign_keys = ON` и WAL.
- Схема: `app/database/init.sql` (идемпотентный скрипт, таблицы `users`, `texts`, `images`, `seo`).
- Инициализация: выполняется в lifespan-хуке приложения (`ensure_database_initialized`).
- Доступ: модуль `app/database/db.py` с хелперами `query_one`, `query_all`, `execute`, `executemany` и словарным `row_factory`.
- Дымовой тест: `smoke_test()` выполняется на старте, логирует результат.

## Этап 2 — аутентификация и безопасность

- Логины через email+пароль, проверка и хэширование с bcrypt.
- JWT access-токен (15 мин) хранится в HttpOnly cookie `access_token`.
- Rate limiting логина: 5 попыток/60 сек (in-memory sliding window).
- CSRF middleware для всех небезопасных методов; токен в cookie + заголовок `x-csrf-token`.
- Защищённый роут `/cms` требует валидного JWT и возвращает простую заглушку JSON.
