## Этап 0 — базовая архитектура и окружение

- Ядро: FastAPI (`app/main.py`) с healthcheck `GET /health`.
- Jinja2 шаблоны: `app/templates` с базовым макетом и партиалами.
- Структура каталогов: `app/{auth,cms,site,static,templates,utils,database}`.
- Конфигурация окружения: `.env` (пример в `.env.example`), загрузка через `python-dotenv`.
- Стили: TailwindCSS 4.1, вход `app/static/css/input.css` (`@import "tailwindcss";`), выход `app/static/css/output.css`; сборка через `@tailwindcss/cli` скрипты в `package.json`.
  - Подключение статики через `app.mount('/static', ...)`.
- Зависимости Python: перечислены в `requirements.txt` (FastAPI, Uvicorn, Jinja2, python-multipart, passlib[bcrypt], PyJWT, Pillow, python-dotenv, email-validator).
- Базовые правила репозитория: `.gitignore`, `.editorconfig`.

Решения:
- Минимальный HTTP‑интерфейс для проверки живости сервиса без БД.
- Базовый UI: `/` рендерится через Jinja2, поддержка светлой/тёмной темы (localStorage + `data-theme`), Tailwind `dark:` включён через `@variant dark (&:where([data-theme="dark"], [data-theme="dark"] *));` в `input.css`.
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
- Защищённые роуты `/cms/*` требуют валидного JWT; доступ проверяется в `AuthRedirectMiddleware` (cookie -> JWT -> пользователь в БД). При отсутствии/некорректности токена выполняется редирект на `/login`.
- Эндпоинты аутентификации:
  - `GET /login` — форма входа (тёмная тема, современный UI)
  - `POST /login` — валидация email, пароль ≥ 8, проверка bcrypt, установка HttpOnly JWT cookie, редирект на `/cms`
  - `GET /register` — форма регистрации (тёмная тема)
  - `POST /register` — валидация email и пароля, проверка уникальности, bcrypt-хэш, автологин, редирект на `/cms`
  - `POST /logout` — удаление cookie и редирект на `/login`

## Этап 3 — шаблоны и базовый UI

- Jinja2 шаблонизация: `app/templates/base.html` с подключением Tailwind, светлая/тёмная тема через `data-theme` атрибут.
- Партиалы: `app/templates/partials/header.html` с переключателем темы и навигацией.
- Статика: монтирование через `app.mount('/static', ...)`, подключение `output.css` в базовом шаблоне.
- Tailwind 4.1: `@import "tailwindcss"` в `input.css`, сборка через `@tailwindcss/cli`, тёмный режим через `@variant dark (&:where([data-theme="dark"], [data-theme="dark"] *));`.
- Роутинг: `/` рендерится через `templates.TemplateResponse("index.html", {"request": request})`.

Решения:
- Базовый UI без WYSIWYG, только `<input>`/`<textarea>` формы.
- Переключение темы сохраняется в localStorage, применяется при загрузке страницы.
- Контейнер с `max-w-6xl` для адаптивности, тёмные классы `dark:` работают корректно.

## Этап 4 — модуль Dashboard

- CMS роуты: `app/cms/routes.py` с защищёнными эндпоинтами `/cms/*`.
- Dashboard: главная панель с приветствием, статистикой и быстрыми ссылками.
- Статистика: подсчёт изображений, языков, текстов, пользователей через SQL-запросы.
- Шаблоны: `dashboard.html`, `texts.html`, `images.html`, `seo.html`, `users.html`.
- Роли: проверка доступа к разделу "Пользователи" только для admin.
- UI: современный дизайн с карточками статистики и быстрыми действиями.

Решения:
- Статистика загружается из БД в реальном времени через функции `get_dashboard_stats()`.
- Разделение доступа по ролям: admin видит все разделы, editor не видит "Пользователи".
- Адаптивный дизайн с использованием Tailwind CSS 4.1 и тёмной темы.
- Заглушки для будущих разделов с информативными сообщениями.