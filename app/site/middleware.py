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
        """
        # Извлекаем язык из URL для всех страниц (включая CMS)
        language = self.extract_language_from_url(request.url.path)
        
        # Сохраняем язык в состоянии запроса
        request.state.language = language
        request.state.supported_languages = self.supported_languages
        request.state.default_language = self.default_language
        
        # Логируем определение языка
        logger.debug(f"Language detected: {language} for path: {request.url.path}")
        
        # Отладочная информация для CMS
        if request.url.path.startswith('/cms/'):
            logger.info(f"CMS Language Debug - Path: {request.url.path}, Language: {language}")
            logger.info(f"CMS Language Debug - Supported languages: {self.supported_languages}")
            logger.info(f"CMS Language Debug - Default language: {self.default_language}")
        
        # Продолжаем обработку запроса
        response = await call_next(request)
        
        return response
    
    def extract_language_from_url(self, path: str) -> str:
        """
        Извлечь язык из URL
        
        Args:
            path: путь URL
            
        Returns:
            Код языка или язык по умолчанию
        """
        # Для CMS роутов проверяем паттерн /cms/{lang}/... или /cms/{lang}
        if path.startswith('/cms/'):
            # Проверяем паттерн /cms/{lang}/... (с дополнительным путем)
            cms_with_path_pattern = re.compile(r'^/cms/([a-z]{2})/(.*)$')
            match = cms_with_path_pattern.match(path)
            if match:
                language = match.group(1)
                if is_language_supported(language):
                    return language
            
            # Проверяем паттерн /cms/{lang} (без дополнительного пути)
            cms_exact_pattern = re.compile(r'^/cms/([a-z]{2})$')
            match = cms_exact_pattern.match(path)
            if match:
                language = match.group(1)
                if is_language_supported(language):
                    return language
        else:
            # Для публичных страниц проверяем обычный паттерн /{lang}/...
            match = LANGUAGE_PATTERN.match(path)
            if match:
                language = match.group(1)
                if is_language_supported(language):
                    return language
        
        # Если язык не найден или не поддерживается, возвращаем язык по умолчанию
        return self.default_language
    
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
        
        # Специальная обработка для CMS роутов
        if current_path.startswith('/cms/'):
            # Для CMS роутов генерируем URL с языковыми префиксами
            # Убираем существующий языковой префикс, если он есть
            clean_path = current_path
            for lang in self.supported_languages:
                if current_path.startswith(f'/cms/{lang}/'):
                    clean_path = f'/cms/{current_path[len(f"/cms/{lang}"):]}'
                    break
                elif current_path == f'/cms/{lang}':
                    clean_path = '/cms/'
                    break
            
            # Нормализуем путь - убираем двойные слеши
            clean_path = clean_path.replace('//', '/')
            
            # Генерируем URL для каждого языка
            for lang in self.supported_languages:
                if lang == self.default_language:
                    # Для языка по умолчанию используем базовый путь
                    urls[lang] = clean_path
                else:
                    # Для других языков добавляем префикс языка
                    if clean_path == '/cms/':
                        urls[lang] = f'/cms/{lang}/'
                    else:
                        # Убираем /cms/ из начала и добавляем языковой префикс
                        sub_path = clean_path[4:] if clean_path.startswith('/cms/') else clean_path
                        urls[lang] = f'/cms/{lang}{sub_path}'
        else:
            # Обычная обработка для публичных страниц
            # Убираем текущий язык из пути, если он есть
            clean_path = current_path
            if current_path.startswith(f'/{current_language}/'):
                clean_path = current_path[len(f'/{current_language}'):]
            elif current_path == f'/{current_language}':
                clean_path = '/'
            
            # Генерируем URL для каждого языка
            for lang in self.supported_languages:
                if lang == self.default_language:
                    # Для языка по умолчанию не добавляем префикс
                    urls[lang] = clean_path
                else:
                    # Для других языков добавляем префикс
                    urls[lang] = f'/{lang}{clean_path}'
        
        return urls

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
    
    # Отладочная информация
    logger.debug(f"get_language_urls_from_request - Path: {current_path}, Language: {current_language}")
    
    # Используем статический метод для генерации URL
    urls = _generate_language_urls(current_path, current_language)
    
    # Отладочная информация
    logger.debug(f"get_language_urls_from_request - Generated URLs: {urls}")
    
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
    
    # Отладочная информация
    logger.debug(f"Generating URLs for path: {current_path}, language: {current_language}")
    
    # Специальная обработка для CMS роутов
    if current_path.startswith('/cms/'):
        # Для CMS роутов генерируем URL с языковыми префиксами
        # Сначала определяем базовый путь без языкового префикса
        
        # Проверяем, есть ли уже языковой префикс в пути
        clean_path = current_path
        for lang in supported_languages:
            if current_path.startswith(f'/cms/{lang}/'):
                # Убираем языковой префикс: /cms/ru/texts -> /cms/texts
                clean_path = f'/cms{current_path[len(f"/cms/{lang}"):]}'
                break
            elif current_path == f'/cms/{lang}':
                # Убираем языковой префикс: /cms/ru -> /cms/
                clean_path = '/cms/'
                break
        
        # Если путь не начинается с языкового префикса, но содержит /cms/, 
        # то это уже базовый путь
        if clean_path == current_path and current_path.startswith('/cms/'):
            # Путь уже базовый, например /cms/texts
            pass
        
        # Нормализуем путь - убираем двойные слеши
        clean_path = clean_path.replace('//', '/')
        
        # Генерируем URL для каждого языка
        # ВАЖНО: Все языки должны иметь префиксы для сохранения языка при переходах
        for lang in supported_languages:
            if clean_path == '/cms/':
                urls[lang] = f'/cms/{lang}/'
            else:
                # Добавляем языковой префикс для всех языков: /cms/texts -> /cms/ru/texts
                sub_path = clean_path[4:] if clean_path.startswith('/cms/') else clean_path
                urls[lang] = f'/cms/{lang}{sub_path}'
        
        # Отладочная информация
        logger.debug(f"CMS URLs generated: {urls}")
        logger.debug(f"Default language: {default_language}, Current language: {current_language}")
        logger.debug(f"Clean path: {clean_path}")
    else:
        # Обычная обработка для публичных страниц
        # Убираем текущий язык из пути, если он есть
        clean_path = current_path
        if current_path.startswith(f'/{current_language}/'):
            clean_path = current_path[len(f'/{current_language}'):]
        elif current_path == f'/{current_language}':
            clean_path = '/'
        
        # Генерируем URL для каждого языка
        for lang in supported_languages:
            if lang == default_language:
                # Для языка по умолчанию не добавляем префикс
                urls[lang] = clean_path
            else:
                # Для других языков добавляем префикс
                urls[lang] = f'/{lang}{clean_path}'
    
    # Отладочная информация
    logger.debug(f"Generated URLs: {urls}")
    
    return urls
