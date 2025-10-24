"""
Конфигурация мультиязычности
"""
import os
from typing import List

# Получаем настройки из переменных окружения
SUPPORTED_LANGUAGES = os.getenv("SUPPORTED_LANGUAGES", "en,ua,ru").split(",")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")

# Валидация языков
def get_supported_languages() -> List[str]:
    """Получить список поддерживаемых языков"""
    return [lang.strip() for lang in SUPPORTED_LANGUAGES if lang.strip()]

def get_default_language() -> str:
    """Получить язык по умолчанию"""
    return DEFAULT_LANGUAGE if DEFAULT_LANGUAGE in get_supported_languages() else "en"

def is_language_supported(language: str) -> bool:
    """Проверить, поддерживается ли язык"""
    return language in get_supported_languages()
