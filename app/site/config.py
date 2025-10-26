"""
Конфигурация мультиязычности
"""
import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()  # Загружает .env файл

# Получаем настройки из переменных окружения
SUPPORTED_LANGUAGES_JSON = os.getenv("SUPPORTED_LANGUAGES", '{"en":{"name":"EN","full_name":"English"}}')
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")

# Парсим JSON конфигурацию языков
try:
    SUPPORTED_LANGUAGES_INFO = json.loads(SUPPORTED_LANGUAGES_JSON)
except json.JSONDecodeError:
    # Fallback к простому формату
    SUPPORTED_LANGUAGES_INFO = {
        "en": {"name": "EN", "full_name": "English"}
    }

# Валидация языков
def get_supported_languages() -> List[str]:
    """Получить список поддерживаемых языков"""
    return list(SUPPORTED_LANGUAGES_INFO.keys())

def get_supported_languages_info() -> Dict[str, Dict[str, str]]:
    """Получить полную информацию о поддерживаемых языках"""
    return SUPPORTED_LANGUAGES_INFO

def get_default_language() -> str:
    """Получить язык по умолчанию"""
    return DEFAULT_LANGUAGE if DEFAULT_LANGUAGE in get_supported_languages() else "en"

def is_language_supported(language: str) -> bool:
    """Проверить, поддерживается ли язык"""
    return language in get_supported_languages()
