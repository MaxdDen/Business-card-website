"""
Публичные роуты сайта-визитки
"""
import logging
from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from app.database.db import query_all, query_one
from app.utils.cache import text_cache, image_cache
from app.site.middleware import get_language_from_request, get_supported_languages_from_request, get_language_urls_from_request, set_language_cookie
from typing import Optional, Dict, Any
import os
from app.site.config import get_default_language

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_text(page: str, key: str, lang: str = get_default_language()) -> str:
    """
    Получить текст из БД с кэшированием
    
    Args:
        page: страница (home, about, catalog, contacts)
        key: ключ поля (title, subtitle, description, etc.)
        lang: язык (en, ua, ru)
    
    Returns:
        Значение текста или пустую строку
    """
    try:
        # Получаем из БД
        result = query_one(
            "SELECT value FROM texts WHERE page = ? AND key = ? AND lang = ?",
            (page, key, lang)
        )
        
        value = result.get("value", "") if result else ""
        return value
        
    except Exception as e:
        logger.error(f"Ошибка получения текста {page}.{key}.{lang}: {e}")
        return ""

def get_seo_data(page: str, lang: str = get_default_language()) -> Dict[str, str]:
    """
    Получить SEO данные для страницы
    
    Args:
        page: страница
        lang: язык
    
    Returns:
        Словарь с title, description, keywords
    """
    try:
        result = query_one(
            "SELECT title, description, keywords FROM seo WHERE page = ? AND lang = ?",
            (page, lang)
        )
        
        seo_data = {
            "title": result.get("title", "") if result else "",
            "description": result.get("description", "") if result else "",
            "keywords": result.get("keywords", "") if result else ""
        }
        
        return seo_data
        
    except Exception as e:
        logger.error(f"Ошибка получения SEO данных {page}.{lang}: {e}")
        return {"title": "", "description": "", "keywords": ""}

def get_image(type: str, order: Optional[int] = None) -> Optional[Dict[str, str]]:
    """
    Получить изображение из БД
    
    Args:
        type: тип изображения (logo, slider, background, favicon)
        order: порядок для слайдера (если None, то первое изображение)
    
    Returns:
        Словарь с path, original_path или None
    """
    try:
        if order is not None:
            # Для слайдера по порядку
            result = query_one(
                "SELECT path, original_path FROM images WHERE type = ? AND \"order\" = ? ORDER BY \"order\"",
                (type, order)
            )
        else:
            # Для других типов - первое изображение
            result = query_one(
                "SELECT path, original_path FROM images WHERE type = ? ORDER BY \"order\" LIMIT 1",
                (type,)
            )
        
        if result:
            return {
                "path": result.get("path", ""),
                "original_path": result.get("original_path", "")
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Ошибка получения изображения {type}: {e}")
        return None

def get_slider_images() -> list:
    """
    Получить все изображения слайдера
    
    Returns:
        Список словарей с path, original_path
    """
    try:
        results = query_all(
            "SELECT path, original_path FROM images WHERE type = 'slider' ORDER BY \"order\""
        )
        
        return [
            {
                "path": row.get("path", ""),
                "original_path": row.get("original_path", "")
            }
            for row in results
        ]
        
    except Exception as e:
        logger.error(f"Ошибка получения слайдера: {e}")
        return []

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Главная страница"""
    # Получаем язык из middleware
    lang = get_language_from_request(request)
    supported_languages = get_supported_languages_from_request(request)
    language_urls = get_language_urls_from_request(request)
    
    # Получаем тексты
    texts = {
        "title": get_text("home", "title", lang),
        "subtitle": get_text("home", "subtitle", lang),
        "description": get_text("home", "description", lang),
        "cta_text": get_text("home", "cta_text", lang)
    }
    
    # Получаем SEO данные
    seo_data = get_seo_data("home", lang)
    
    # Получаем изображения
    logo = get_image("logo")
    background = get_image("background")
    slider_images = get_slider_images()
    
    return templates.TemplateResponse("public/home.html", {
        "request": request,
        "lang": lang,
        "texts": texts,
        "seo": seo_data,
        "logo": logo,
        "background": background,
        "slider_images": slider_images,
        "supported_languages": supported_languages,
        "language_urls": language_urls
    })

@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """Страница о компании"""
    # Получаем язык из middleware
    lang = get_language_from_request(request)
    supported_languages = get_supported_languages_from_request(request)
    language_urls = get_language_urls_from_request(request)
    
    texts = {
        "title": get_text("about", "title", lang),
        "subtitle": get_text("about", "subtitle", lang),
        "description": get_text("about", "description", lang)
    }
    
    seo_data = get_seo_data("about", lang)
    
    return templates.TemplateResponse("public/about.html", {
        "request": request,
        "lang": lang,
        "texts": texts,
        "seo": seo_data,
        "supported_languages": supported_languages,
        "language_urls": language_urls
    })

@router.get("/catalog", response_class=HTMLResponse)
async def catalog(request: Request):
    """Страница каталога"""
    # Получаем язык из middleware
    lang = get_language_from_request(request)
    supported_languages = get_supported_languages_from_request(request)
    language_urls = get_language_urls_from_request(request)
    
    texts = {
        "title": get_text("catalog", "title", lang),
        "subtitle": get_text("catalog", "subtitle", lang),
        "description": get_text("catalog", "description", lang)
    }
    
    seo_data = get_seo_data("catalog", lang)
    
    return templates.TemplateResponse("public/catalog.html", {
        "request": request,
        "lang": lang,
        "texts": texts,
        "seo": seo_data,
        "supported_languages": supported_languages,
        "language_urls": language_urls
    })

@router.get("/contacts", response_class=HTMLResponse)
async def contacts(request: Request):
    """Страница контактов"""
    # Получаем язык из middleware
    lang = get_language_from_request(request)
    supported_languages = get_supported_languages_from_request(request)
    language_urls = get_language_urls_from_request(request)
    
    texts = {
        "title": get_text("contacts", "title", lang),
        "subtitle": get_text("contacts", "subtitle", lang),
        "description": get_text("contacts", "description", lang),
        "phone": get_text("contacts", "phone", lang),
        "address": get_text("contacts", "address", lang)
    }
    
    seo_data = get_seo_data("contacts", lang)
    
    return templates.TemplateResponse("public/contacts.html", {
        "request": request,
        "lang": lang,
        "texts": texts,
        "seo": seo_data,
        "supported_languages": supported_languages,
        "language_urls": language_urls
    })

# Мультиязычные алиасы
@router.get("/ru/", response_class=HTMLResponse)
async def home_ru(request: Request):
    return await home(request)

@router.get("/en/", response_class=HTMLResponse)
async def home_en(request: Request):
    return await home(request)

@router.get("/ua/", response_class=HTMLResponse)
async def home_ua(request: Request):
    return await home(request)

@router.get("/ru/about", response_class=HTMLResponse)
async def about_ru(request: Request):
    return await about(request)

@router.get("/en/about", response_class=HTMLResponse)
async def about_en(request: Request):
    return await about(request)

@router.get("/ua/about", response_class=HTMLResponse)
async def about_ua(request: Request):
    return await about(request)

@router.get("/ru/catalog", response_class=HTMLResponse)
async def catalog_ru(request: Request):
    return await catalog(request)

@router.get("/en/catalog", response_class=HTMLResponse)
async def catalog_en(request: Request):
    return await catalog(request)

@router.get("/ua/catalog", response_class=HTMLResponse)
async def catalog_ua(request: Request):
    return await catalog(request)

@router.get("/ru/contacts", response_class=HTMLResponse)
async def contacts_ru(request: Request):
    return await contacts(request)

@router.get("/en/contacts", response_class=HTMLResponse)
async def contacts_en(request: Request):
    return await contacts(request)

@router.get("/ua/contacts", response_class=HTMLResponse)
async def contacts_ua(request: Request):
    return await contacts(request)

# API endpoint для переключения языка
@router.post("/api/set-language")
async def set_language_api(language: str = Form(...)):
    """
    API endpoint для программного переключения языка
    Устанавливает cookie с выбранным языком
    """
    from app.site.config import is_language_supported
    
    # Проверяем, поддерживается ли язык
    if not is_language_supported(language):
        raise HTTPException(status_code=400, detail=f"Language '{language}' is not supported")
    
    # Создаем JSON ответ с cookie
    response = JSONResponse(content={"success": True, "language": language})
    set_language_cookie(response, language)
    
    return response
