"""
Глобальные API endpoints
"""
import logging
from fastapi import APIRouter
from typing import Dict, Any
from app.site.config import get_supported_languages, get_default_language

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/supported-languages")
async def get_supported_languages_api() -> Dict[str, Any]:
    """
    Получить список поддерживаемых языков и язык по умолчанию
    
    Returns:
        Словарь с информацией о поддерживаемых языках
    """
    try:
        languages = get_supported_languages()
        
        # Маппинг названий языков (короткие коды)
        language_names = {
            'ru': 'RU',
            'en': 'EN', 
            'ua': 'UA'
        }
        
        # Полные названия языков
        language_full_names = {
            'ru': 'Русский',
            'en': 'English',
            'ua': 'Українська'
        }
        
        # Создаем объект с информацией о языках
        languages_info = {}
        for lang in languages:
            languages_info[lang] = {
                'code': lang,
                'name': language_names.get(lang, lang.upper()),
                'full_name': language_full_names.get(lang, lang)
            }
        
        return {
            "success": True,
            "languages": languages,  # Массив кодов для обратной совместимости
            "languages_info": languages_info,  # Объект с полной информацией
            "default_language": get_default_language()
        }
    except Exception as e:
        logger.error(f"Error getting supported languages: {e}")
        return {
            "success": False,
            "message": "Error getting supported languages",
            "languages": ["en"],
            "languages_info": {"en": {"code": "en", "name": "EN", "full_name": "English"}},
            "default_language": "en"
        }