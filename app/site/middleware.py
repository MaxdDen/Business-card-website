"""
Middleware для обработки мультиязычности
Автоматическое определение языка из URL и сохранение в контексте запроса
"""
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import re
from app.site.config import get_supported_languages, get_default_language, is_language_supported

logger = logging.getLogger(__name__)

# Регулярное выражение для извлечения языка из URL
LANGUAGE_PATTERN = re.compile(r'^/([a-z]{2})(?:/|$)')

class LanguageMiddleware(BaseHTTPMiddleware):
    """
    Middleware для автоматического определения языка из URL
    """
    
    def __init__(self, app, supported_languages: list = None, default_language: str = None):
        super().__init__(app)
        self.supported_languages = supported_languages or get_supported_languages()
        self.default_language = default_language or get_default_language()
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Обработка запроса для определения языка
        Поддерживает URL-based и cookie-based подходы
        """
        # 1. Сначала пытаемся извлечь язык из URL
        language_from_url = self.extract_language_from_url(request.url.path)
        
        # 2. Проверяем cookie с предпочтением пользователя
        language_from_cookie = request.cookies.get("user_language")
        
        # 3. Определяем приоритет: URL > Cookie > Default
        if language_from_url is not None:
            # Если в URL есть язык, используем его
            language = language_from_url
        elif language_from_cookie and is_language_supported(language_from_cookie):
            # Если в URL нет языка, но есть в cookie, используем cookie
            language = language_from_cookie
        else:
            # Иначе используем язык по умолчанию
            language = self.default_language
        
        # Сохраняем язык в состоянии запроса
        request.state.language = language
        request.state.supported_languages = self.supported_languages
        request.state.default_language = self.default_language
        
        # Логируем определение языка
        logger.debug(f"Language detected: {language} (URL: {language_from_url}, Cookie: {language_from_cookie}) for path: {request.url.path}")
        
        # Продолжаем обработку запроса
        response = await call_next(request)
        
        # 4. Сохраняем выбранный язык в cookie для будущих посещений
        # (только если язык был определен из URL)
        if language_from_url is not None:
            self.set_language_cookie(response, language)
        
        return response
    
    def extract_language_from_url(self, path: str) -> str:
        """
        Извлечь язык из URL
        
        Args:
            path: путь URL
            
        Returns:
            Код языка или None если язык не найден в URL
        """
        # НОВАЯ СТРУКТУРА: домен → язык → страница
        # Универсальная проверка для всех типов страниц: /{lang}/...
        match = LANGUAGE_PATTERN.match(path)
        if match:
            language = match.group(1)
            if is_language_supported(language):
                return language
        
        # Если язык не найден в URL, возвращаем None
        return None
    
    def get_language_urls(self, current_path: str, current_language: str) -> dict:
        """
        Получить URLs для всех языков на основе текущего пути
        
        Args:
            current_path: текущий путь
            current_language: текущий язык
            
        Returns:
            Словарь с URL для каждого языка
        """
        urls = {}
        
        # НОВАЯ СТРУКТУРА: домен → язык → страница
        # Универсальная обработка для всех типов страниц
        
        # Убираем текущий язык из пути, если он есть
        clean_path = current_path
        for lang in self.supported_languages:
            if current_path.startswith(f'/{lang}/'):
                clean_path = current_path[len(f'/{lang}'):]
                break
            elif current_path == f'/{lang}':
                clean_path = '/'
                break
        
        # Нормализуем путь - убираем двойные слеши
        clean_path = clean_path.replace('//', '/')
        
        # Генерируем URL для каждого языка
        # ВАЖНО: Все языки должны иметь префиксы для консистентности
        for lang in self.supported_languages:
            if clean_path == '/':
                urls[lang] = f'/{lang}/'
            else:
                urls[lang] = f'/{lang}{clean_path}'
        
        return urls
    
    def set_language_cookie(self, response: Response, language: str) -> None:
        """
        Установить cookie с выбранным языком
        
        Args:
            response: объект ответа
            language: код языка
        """
        response.set_cookie(
            key="user_language",
            value=language,
            max_age=365*24*60*60,  # 1 год
            httponly=False,  # Доступен для JavaScript
            samesite="lax",
            secure=False  # Для development, в production должно быть True
        )
    
    def get_language_from_cookie(self, request: Request) -> str:
        """
        Получить язык из cookie
        
        Args:
            request: объект запроса
            
        Returns:
            Код языка из cookie или None
        """
        return request.cookies.get("user_language")

def get_language_from_request(request: Request) -> str:
    """
    Получить язык из состояния запроса
    
    Args:
        request: объект запроса
        
    Returns:
        Код языка
    """
    return getattr(request.state, 'language', get_default_language())

def get_supported_languages_from_request(request: Request) -> list:
    """
    Получить список поддерживаемых языков из состояния запроса
    
    Args:
        request: объект запроса
        
    Returns:
        Список поддерживаемых языков
    """
    return getattr(request.state, 'supported_languages', get_supported_languages())

def get_language_urls_from_request(request: Request) -> dict:
    """
    Получить URLs для всех языков из состояния запроса
    
    Args:
        request: объект запроса
        
    Returns:
        Словарь с URL для каждого языка
    """
    current_language = get_language_from_request(request)
    current_path = request.url.path
    
    # Используем статический метод для генерации URL
    urls = _generate_language_urls(current_path, current_language)
    
    return urls

def _generate_language_urls(current_path: str, current_language: str) -> dict:
    """
    Генерировать URLs для всех языков
    
    Args:
        current_path: текущий путь
        current_language: текущий язык
        
    Returns:
        Словарь с URL для каждого языка
    """
    from app.site.config import get_supported_languages, get_default_language
    
    supported_languages = get_supported_languages()
    default_language = get_default_language()
    urls = {}
    
    # НОВАЯ СТРУКТУРА: домен → язык → страница
    # Универсальная обработка для всех типов страниц
    
    # Убираем текущий язык из пути, если он есть
    clean_path = current_path
    for lang in supported_languages:
        if current_path.startswith(f'/{lang}/'):
            clean_path = current_path[len(f'/{lang}'):]
            break
        elif current_path == f'/{lang}':
            clean_path = '/'
            break
    
    # Нормализуем путь - убираем двойные слеши
    clean_path = clean_path.replace('//', '/')
    
    # Генерируем URL для каждого языка
    # Скрываем дефолтный язык из URL
    for lang in supported_languages:
        if lang == default_language:
            # Для дефолтного языка не добавляем префикс
            if clean_path == '/':
                urls[lang] = '/'
            elif clean_path == '/login':
                urls[lang] = '/login'
            elif clean_path == '/register':
                urls[lang] = '/register'
            else:
                urls[lang] = clean_path
        else:
            # Для других языков добавляем префикс
            if clean_path == '/':
                urls[lang] = f'/{lang}/'
            elif clean_path == '/login':
                urls[lang] = f'/{lang}/login'
            elif clean_path == '/register':
                urls[lang] = f'/{lang}/register'
            else:
                urls[lang] = f'/{lang}{clean_path}'
    
    return urls

def set_language_cookie(response: Response, language: str) -> None:
    """
    Установить cookie с выбранным языком (standalone функция)
    
    Args:
        response: объект ответа
        language: код языка
    """
    response.set_cookie(
        key="user_language",
        value=language,
        max_age=365*24*60*60,  # 1 год
        httponly=False,  # Доступен для JavaScript
        samesite="lax",
        secure=False  # Для development, в production должно быть True
    )

def get_language_from_cookie(request: Request) -> str:
    """
    Получить язык из cookie (standalone функция)
    
    Args:
        request: объект запроса
        
    Returns:
        Код языка из cookie или None
    """
    return request.cookies.get("user_language")

def clear_language_cookie(response: Response) -> None:
    """
    Очистить cookie с языком
    
    Args:
        response: объект ответа
    """
    response.delete_cookie(
        key="user_language",
        samesite="lax"
    )

def get_cms_url(path: str, lang: str = None) -> str:
    """
    Получить URL для CMS с учетом дефолтного языка
    
    Args:
        path: путь без языкового префикса (например, "texts", "images")
        lang: язык (если None, используется текущий из контекста)
        
    Returns:
        URL с языковым префиксом или без него для дефолтного языка
    """
    from app.site.config import get_default_language
    
    if lang is None:
        # Если язык не передан, используем дефолтный
        lang = get_default_language()
    
    default_lang = get_default_language()
    
    # Если это дефолтный язык, не добавляем префикс
    if lang == default_lang:
        return f"/cms/{path}"
    else:
        return f"/{lang}/cms/{path}"

def get_cms_dashboard_url(lang: str = None) -> str:
    """
    Получить URL для дашборда CMS с учетом дефолтного языка
    
    Args:
        lang: язык (если None, используется текущий из контекста)
        
    Returns:
        URL с языковым префиксом или без него для дефолтного языка
    """
    from app.site.config import get_default_language
    
    if lang is None:
        lang = get_default_language()
    
    default_lang = get_default_language()
    
    # Если это дефолтный язык, не добавляем префикс
    if lang == default_lang:
        return "/cms/"
    else:
        return f"/{lang}/cms/"