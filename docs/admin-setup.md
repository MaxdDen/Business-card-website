# Настройка администратора

## Автоматическое создание администратора

При запуске приложения автоматически проверяется наличие пользователя-администратора. Если администратор не найден, он создается автоматически на основе переменных окружения.

## Переменные окружения

Создайте файл `.env` в корне проекта со следующими переменными:

```env
# Database configuration
DATABASE_PATH=data/app.db

# JWT Configuration
JWT_SECRET=your-secret-key-here-change-this-in-production
JWT_EXPIRES_MINUTES=15

# Cookie Configuration
COOKIE_SAMESITE=lax
COOKIE_SECURE=false

# Admin User Configuration
# Эти переменные используются для создания администратора
DATABASE_ROOT=admin@example.com
DATABASE_ROOT_PASS=admin123456

# Development settings
DEBUG=true
```

## Роли пользователей

- **admin** - Администратор с полными правами доступа
- **editor** - Редактор с ограниченными правами (создается при регистрации)

## Безопасность

⚠️ **ВАЖНО**: Обязательно измените значения `DATABASE_ROOT`, `DATABASE_ROOT_PASS` и `JWT_SECRET` в продакшене!

- Используйте сложные пароли для администратора
- Храните `.env` файл в безопасности
- Не коммитьте `.env` файл в репозиторий

## Проверка работы

После запуска приложения в логах должно появиться сообщение:
```
Created admin user admin@example.com with ID 1
```

Или если администратор уже существует:
```
Admin user admin@example.com already exists
```
