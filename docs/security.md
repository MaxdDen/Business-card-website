# Безопасность CMS

## Обзор

Система безопасности CMS реализована согласно современным стандартам и best practices. Этап 12 включает комплексную защиту от основных угроз веб-приложений.

## Реализованные меры безопасности

### 1. Security Headers

Все HTTP-ответы содержат заголовки безопасности:

- **Content-Security-Policy (CSP)** - защита от XSS и инъекций кода
- **X-Frame-Options: DENY** - защита от clickjacking атак
- **X-Content-Type-Options: nosniff** - предотвращение MIME-sniffing
- **X-XSS-Protection** - дополнительная защита от XSS (legacy браузеры)
- **Referrer-Policy** - контроль передачи referrer информации
- **Permissions-Policy** - ограничение браузерных API
- **Strict-Transport-Security** - принудительное использование HTTPS (только production)

### 2. Безопасные Cookies

JWT токены и другие cookies устанавливаются с правильными флагами:

- **HttpOnly** - защита от доступа через JavaScript
- **SameSite=Lax** - защита от CSRF атак
- **Secure** - передача только через HTTPS (автоматически в production)

### 3. Валидация входных данных

#### Email
- Проверка формата через регулярное выражение
- Ограничение длины (максимум 255 символов)
- Нормализация адреса

#### Пароли
- Минимальная длина: 8 символов
- Обязательно наличие букв И цифр
- Максимальная длина: 72 байта (ограничение bcrypt)
- Хэширование через bcrypt с автоматической солью

#### Текстовый контент
- Ограничение максимальной длины (10,000 символов по умолчанию)
- Удаление управляющих символов
- Экранирование HTML при необходимости

#### Файлы
- Белый список расширений: `.jpg`, `.jpeg`, `.png`, `.webp`, `.ico`
- Проверка MIME типа
- Максимальный размер: 2MB
- Валидация что файл является реальным изображением
- Очистка имен файлов от опасных символов
- Защита от path traversal (../, .\, etc.)

### 4. Защита от атак

#### SQL Injection
- Использование параметризованных запросов
- Никогда не используется конкатенация SQL
- Обнаружение подозрительных паттернов (UNION SELECT, DROP TABLE, etc.)

#### XSS (Cross-Site Scripting)
- Автоматическое экранирование в Jinja2 шаблонах
- Функция `sanitize_html()` для принудительного экранирования
- CSP headers блокируют inline scripts
- Обнаружение XSS векторов (`<script>`, `javascript:`, event handlers)

#### CSRF (Cross-Site Request Forgery)
- CSRF middleware для всех небезопасных методов (POST, PUT, DELETE)
- Автоматическая генерация и проверка токенов
- API endpoints исключены из CSRF проверки (используют другие механизмы)

#### Clickjacking
- X-Frame-Options: DENY блокирует embedding в iframe
- CSP frame-ancestors директива

#### Path Traversal
- Очистка имен файлов от `../`, `.\` и подобных паттернов
- Использование UUID для генерации имен файлов
- Проверка что путь находится внутри разрешенной директории

### 5. Rate Limiting

Защита от brute-force атак:

- **Логин**: максимум 5 попыток за 60 секунд
- Sliding window алгоритм
- In-memory хранение счетчиков
- Настраивается через переменные окружения

### 6. Настройка Production

Для production окружения установите переменную:

```env
ENVIRONMENT=production
```

Это автоматически включит:
- Secure флаг для всех cookies (требует HTTPS)
- Strict-Transport-Security заголовок
- Усиленные настройки безопасности

## Использование

### Установка безопасных cookies

```python
from app.auth.security_headers import set_secure_cookie

set_secure_cookie(
    response=response,
    key="my_cookie",
    value="cookie_value",
    max_age=3600,
    httponly=True,
    samesite="lax"
)
```

### Валидация данных

```python
from app.utils.validation import (
    validate_email,
    validate_password,
    sanitize_filename,
    detect_sql_injection
)

# Валидация email
is_valid, error = validate_email("user@example.com")
if not is_valid:
    return {"error": error}

# Валидация пароля
is_valid, error = validate_password("MyPass123")
if not is_valid:
    return {"error": error}

# Очистка имени файла
safe_name = sanitize_filename("../../etc/passwd.jpg")
# Результат: "______etc_passwd.jpg"

# Проверка на SQL инъекцию
if detect_sql_injection(user_input):
    return {"error": "Подозрительная активность"}
```

## Тестирование безопасности

Запустите комплексный тест безопасности:

```bash
python manage_tests.py security
```

Тест проверяет:
- ✅ Security Headers
- ✅ Безопасность Cookies
- ✅ Ограничение размера файлов
- ✅ Валидацию формата файлов
- ✅ Защиту от SQL инъекций
- ✅ Защиту от XSS
- ✅ Rate Limiting
- ✅ Валидацию паролей
- ✅ Очистку имен файлов

## Рекомендации

### Development

1. Используйте HTTPS даже в development (self-signed сертификат)
2. Регулярно запускайте тесты безопасности
3. Обновляйте зависимости для закрытия уязвимостей

### Production

1. **Обязательно** установите `ENVIRONMENT=production`
2. Используйте сильный `JWT_SECRET` (минимум 32 случайных символа)
3. Настройте HTTPS на уровне веб-сервера (nginx/apache)
4. Регулярно делайте бэкапы БД
5. Мониторьте логи на подозрительную активность
6. Используйте firewall для ограничения доступа к порту приложения

### Переменные окружения

Обязательные для безопасности:

```env
# Секретный ключ для JWT (ОБЯЗАТЕЛЬНО изменить!)
JWT_SECRET=your-super-secret-key-change-this-in-production

# Окружение (development/production)
ENVIRONMENT=production

# Время жизни JWT токена (минуты)
JWT_EXPIRES_MINUTES=15

# Rate limiting для логина
LOGIN_MAX_ATTEMPTS=5
LOGIN_WINDOW_SECONDS=60
```

## Известные ограничения

1. **In-memory rate limiting** - сбрасывается при перезапуске сервера. Для production рассмотрите Redis.
2. **Session management** - используется только access token без refresh token. Для длительных сессий может потребоваться расширение.
3. **Audit logging** - не реализовано. Рассмотрите добавление для production.

## Дополнительные улучшения (опционально)

Для максимальной безопасности рассмотрите:

1. **Redis для rate limiting** - персистентное хранилище счетчиков
2. **Audit logging** - журналирование всех действий пользователей
3. **2FA** - двухфакторная аутентификация
4. **IP whitelisting** - ограничение доступа к CMS по IP
5. **Automated security scanning** - регулярное сканирование на уязвимости
6. **WAF (Web Application Firewall)** - дополнительный уровень защиты

## Ссылки

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CSP Documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [Secure Cookie Attributes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies#restrict_access_to_cookies)

