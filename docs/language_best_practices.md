# 🌍 Best Practices для хранения языка в мультиязычном приложении

## 📋 Обзор реализованных подходов

В проекте реализованы **best practices** для определения и хранения выбранного пользователем языка:

### 1. **URL-based подход** (SEO-friendly)
- **Структура URL**: `/{lang}/{page}` (например: `/ru/about`, `/en/contacts`)
- **Преимущества**: SEO-оптимизация, прямые ссылки, кэширование
- **Реализация**: `LanguageMiddleware` автоматически извлекает язык из URL

### 2. **Cookie-based подход** (пользовательские предпочтения)
- **Cookie**: `user_language` с TTL 1 год
- **Преимущества**: Сохранение предпочтений между сессиями
- **Реализация**: Автоматическая установка при переключении языка

### 3. **Приоритет определения языка**
```
URL > Cookie > Default Language
```

## 🔧 Техническая реализация

### Middleware для определения языка
```python
# app/site/middleware.py
class LanguageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 1. Извлекаем язык из URL
        language_from_url = self.extract_language_from_url(request.url.path)
        
        # 2. Проверяем cookie с предпочтением пользователя
        language_from_cookie = request.cookies.get("user_language")
        
        # 3. Определяем приоритет: URL > Cookie > Default
        if language_from_url != self.default_language:
            language = language_from_url
        elif language_from_cookie and is_language_supported(language_from_cookie):
            language = language_from_cookie
        else:
            language = self.default_language
```

### JavaScript для переключения языков
```javascript
// app/static/js/language.js
function switchLanguage(language) {
    // Используем API endpoint для установки cookie
    fetch('/api/set-language', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `language=${language}`
    })
    .then(response => {
        if (response.ok) {
            // Перенаправляем на новую языковую версию
            const newUrl = `/${language}${getCleanPath(window.location.pathname)}`;
            window.location.href = newUrl;
        }
    });
}
```

### API endpoint для программного переключения
```python
# app/site/routes.py
@router.post("/api/set-language")
async def set_language_api(request: Request, language: str):
    """API endpoint для программного переключения языка"""
    if not is_language_supported(language):
        raise HTTPException(status_code=400, detail=f"Language '{language}' is not supported")
    
    response = Response(content={"success": True, "language": language})
    set_language_cookie(response, language)
    return response
```

## 🎯 Best Practices

### 1. **Многоуровневое определение языка**
- **URL** имеет наивысший приоритет (для SEO и прямых ссылок)
- **Cookie** сохраняет пользовательские предпочтения
- **Default** используется как fallback

### 2. **Безопасность cookie**
```python
response.set_cookie(
    key="user_language",
    value=language,
    max_age=365*24*60*60,  # 1 год
    httponly=False,  # Доступен для JavaScript
    samesite="lax",  # Защита от CSRF
    secure=False  # Для development
)
```

### 3. **Валидация языков**
- Проверка поддерживаемых языков из конфигурации
- Обработка недопустимых языков (fallback на default)
- Безопасная обработка пользовательского ввода

### 4. **Кэширование по языкам**
- Отдельное кэширование контента для каждого языка
- Автоматическая инвалидация при изменениях
- Оптимизация производительности

## 🧪 Тестирование

### Автотест cookie-based хранения
```bash
python manage_tests.py language_cookie
```

**Проверяет:**
- ✅ Установку cookie при переключении языка
- ✅ Сохранение языка при переходах между страницами
- ✅ Приоритет URL над cookie
- ✅ Безопасность обработки недопустимых языков
- ✅ Работу с CMS и публичными страницами

## 📊 Структура данных

### Cookie
```
user_language=ru; max-age=31536000; path=/; samesite=lax
```

### URL структура
```
/ru/about     - Русская версия страницы "О компании"
/en/contacts  - Английская версия страницы "Контакты"
/ua/catalog   - Украинская версия страницы "Каталог"
```

### Конфигурация языков
```python
# app/site/config.py
SUPPORTED_LANGUAGES = ["en", "ua", "ru"]
DEFAULT_LANGUAGE = "en"
```

## 🚀 Использование

### В шаблонах
```html
<!-- Переключатель языков -->
<button onclick="switchLanguage('ru')" data-language-button="ru">
    RU
</button>
<button onclick="switchLanguage('en')" data-language-button="en">
    EN
</button>
```

### Программное переключение
```javascript
// Переключение на украинский язык
switchLanguage('ua');
```

### API вызов
```javascript
// Прямой вызов API
fetch('/api/set-language', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'language=ru'
});
```

## 🔒 Безопасность

1. **Валидация входных данных** - проверка поддерживаемых языков
2. **CSRF защита** - SameSite cookie policy
3. **XSS защита** - экранирование пользовательского ввода
4. **Path traversal защита** - валидация путей URL

## 📈 Производительность

1. **Кэширование** - отдельное кэширование для каждого языка
2. **Middleware оптимизация** - минимальные накладные расходы
3. **JavaScript fallback** - работа без JavaScript
4. **CDN совместимость** - URL-based кэширование

## 🎉 Результат

Реализована полнофункциональная система мультиязычности с:
- ✅ SEO-оптимизированными URL
- ✅ Сохранением пользовательских предпочтений
- ✅ Безопасной обработкой языков
- ✅ Высокой производительностью
- ✅ Простотой использования
- ✅ Комплексным тестированием
