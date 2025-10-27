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
        page: страница (динамически определяется из app/templates/public/)
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


def get_all_texts_for_page(page: str, lang: str = get_default_language()) -> dict:
    """
    Получить все тексты для страницы из БД
    
    Args:
        page: страница (динамически определяется из app/templates/public/)
        lang: язык (en, ua, ru)
    
    Returns:
        Словарь {ключ: значение} со всеми текстами страницы
    """
    try:
        # Получаем все тексты для страницы и языка
        results = query_all(
            "SELECT key, value FROM texts WHERE page = ? AND lang = ?",
            (page, lang)
        )
        
        # Преобразуем в словарь
        texts = {}
        for row in results:
            texts[row["key"]] = row["value"]
        
        logger.debug(f"Загружено {len(texts)} текстов для {page}.{lang}: {list(texts.keys())}")
        return texts
        
    except Exception as e:
        logger.error(f"Ошибка получения всех текстов для {page}.{lang}: {e}")
        return {}


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

def get_image_with_alt(type: str, lang: str = get_default_language(), order: Optional[int] = None) -> Optional[Dict[str, str]]:
    """
    Получить изображение с alt-текстом из БД
    
    Args:
        type: тип изображения (logo, slider, background, favicon)
        lang: язык для alt-текста
        order: порядок для слайдера (если None, то первое изображение)
    
    Returns:
        Словарь с path, original_path, alt или None
    """
    try:
        if order is not None:
            # Для слайдера по порядку
            result = query_one(
                """SELECT i.path, i.original_path, ia.alt_text 
                   FROM images i 
                   LEFT JOIN images_alts ia ON i.id = ia.image_id AND ia.lang = ?
                   WHERE i.type = ? AND i."order" = ? 
                   ORDER BY i."order" LIMIT 1""",
                (lang, type, order)
            )
        else:
            # Для других типов - первое изображение
            result = query_one(
                """SELECT i.path, i.original_path, ia.alt_text 
                   FROM images i 
                   LEFT JOIN images_alts ia ON i.id = ia.image_id AND ia.lang = ?
                   WHERE i.type = ? 
                   ORDER BY i."order" LIMIT 1""",
                (lang, type)
            )
        
        if result:
            return {
                "path": result.get("path", ""),
                "original_path": result.get("original_path", ""),
                "alt": result.get("alt_text", "")
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Ошибка получения изображения {type}: {e}")
        return None

def get_slider_images_with_alt(lang: str = get_default_language()) -> list:
    """
    Получить все изображения слайдера с alt-текстами
    
    Args:
        lang: язык для alt-текстов
    
    Returns:
        Список словарей с path, original_path, alt
    """
    try:
        results = query_all(
            """SELECT i.path, i.original_path, ia.alt_text 
               FROM images i 
               LEFT JOIN images_alts ia ON i.id = ia.image_id AND ia.lang = ?
               WHERE i.type = 'slider' 
               ORDER BY i."order\"""",
            (lang,)
        )
        
        return [
            {
                "path": row.get("path", ""),
                "original_path": row.get("original_path", ""),
                "alt": row.get("alt_text", "")
            }
            for row in results
        ]
        
    except Exception as e:
        logger.error(f"Ошибка получения слайдера: {e}")
        return []


def get_all_images_for_template(lang: str = get_default_language()) -> Dict[str, str]:
    """
    Получить все изображения для шаблона в новом формате
    
    Args:
        lang: язык для alt-текстов
    
    Returns:
        Словарь с переменными изображений в формате images.ключ
    """
    try:
        # Получаем все изображения с alt-текстами
        logo = get_image_with_alt("logo", lang)
        background = get_image_with_alt("background", lang)
        favicon = get_image_with_alt("favicon", lang)
        slider_images = get_slider_images_with_alt(lang)
        
        images = {}
        
        # Основные изображения
        if logo:
            images["logo"] = logo.get("path", "")
            images["logo_alt"] = logo.get("alt", "")
        
        if background:
            images["background"] = background.get("path", "")
            images["background_alt"] = background.get("alt", "")
        
        if favicon:
            images["favicon"] = favicon.get("path", "")
            images["favicon_alt"] = favicon.get("alt", "")
        
        # Слайдер изображения
        for i, slider_img in enumerate(slider_images, 1):
            if slider_img:
                images[f"slider{i}"] = slider_img.get("path", "")
                images[f"slider{i}_alt"] = slider_img.get("alt", "")
        
        # Заполняем пустые слоты слайдера
        for i in range(len(slider_images) + 1, 5):
            images[f"slider{i}"] = ""
            images[f"slider{i}_alt"] = ""
        
        return images
        
    except Exception as e:
        logger.error(f"Ошибка получения переменных изображений: {e}")
        return {}


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Главная страница"""
    # Получаем язык из middleware
    lang = get_language_from_request(request)
    supported_languages = get_supported_languages_from_request(request)
    language_urls = get_language_urls_from_request(request)
    
    # Получаем все тексты динамически
    texts = get_all_texts_for_page("home", lang)
    
    # Получаем SEO данные
    seo_data = get_seo_data("home", lang)
    
    # Получаем изображения в новом формате
    images = get_all_images_for_template(lang)
    
    return templates.TemplateResponse("public/home.html", {
        "request": request,
        "lang": lang,
        "texts": texts,
        "seo": seo_data,
        "images": images,
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
    
    # Получаем все тексты динамически
    texts = get_all_texts_for_page("about", lang)
    
    # Получаем SEO данные
    seo_data = get_seo_data("about", lang)
    
    # Получаем изображения в новом формате
    images = get_all_images_for_template(lang)
    
    return templates.TemplateResponse("public/about.html", {
        "request": request,
        "lang": lang,
        "texts": texts,
        "seo": seo_data,
        "images": images,
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
    
    # Получаем все тексты динамически
    texts = get_all_texts_for_page("catalog", lang)
    
    # Получаем SEO данные
    seo_data = get_seo_data("catalog", lang)
    
    # Получаем изображения в новом формате
    images = get_all_images_for_template(lang)
    
    return templates.TemplateResponse("public/catalog.html", {
        "request": request,
        "lang": lang,
        "texts": texts,
        "seo": seo_data,
        "images": images,
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
    
    # Получаем все тексты динамически
    texts = get_all_texts_for_page("contacts", lang)
    
    # Получаем SEO данные
    seo_data = get_seo_data("contacts", lang)
    
    # Получаем изображения в новом формате
    images = get_all_images_for_template(lang)
    
    return templates.TemplateResponse("public/contacts.html", {
        "request": request,
        "lang": lang,
        "texts": texts,
        "seo": seo_data,
        "images": images,
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


# API endpoint для получения публичных переводов
@router.get("/api/translations")
async def get_public_translations(module: str, lang: str = None, request: Request = None):
    """Получить переводы для публичных страниц"""
    try:
        # Если язык не указан, получаем из запроса
        if not lang:
            lang = get_language_from_request(request)
        
        # Валидация модулей для публичных страниц
        valid_modules = ["header"]
        if module not in valid_modules:
            return {"success": False, "message": f"Недопустимый модуль. Доступные: {', '.join(valid_modules)}"}
        
        return {
            "success": True,
            "translations": translations,
            "module": module,
            "lang": lang
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения публичных переводов: {e}")
        return {"success": False, "message": "Ошибка получения переводов"}
