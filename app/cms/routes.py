from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, RedirectResponse
from app.auth.security import get_current_user, create_access_token, decode_token, hash_password
from app.database.db import query_one, query_all, execute
from app.utils.cache import text_cache, image_cache
from app.site.middleware import get_language_from_request, get_supported_languages_from_request, get_language_urls_from_request, get_cms_url
from app.site.config import get_default_language, get_supported_languages
from app.site.routes import get_text
from app.utils.template_parser import TemplateParser
from app.utils.images import (
    validate_image_file, optimize_image, save_original_image, 
    generate_unique_filename, get_image_info
)
from app.auth.security_headers import set_secure_cookie
from typing import Dict, Any, List
import logging
import json
import os
import io
import uuid
from datetime import datetime, timezone
from pathlib import Path
from app.site.config import get_supported_languages

router = APIRouter(tags=["cms"])
templates = Jinja2Templates(directory="app/templates")

logger = logging.getLogger(__name__)


def get_crm_text(page: str, key: str, lang: str = get_default_language()) -> str:
    """
    Получить текст из БД texts_crm с кэшированием
    
    Args:
        page: страница (dashboard, cms_texts, cms_images, etc.)
        key: ключ поля (title, subtitle, description, etc.)
        lang: язык (en, ua, ru)
    
    Returns:
        Значение текста или пустую строку
    """
    try:
        # Получаем из БД
        result = query_one(
            "SELECT value FROM texts_crm WHERE page = ? AND key = ? AND lang = ?",
            (page, key, lang)
        )
        
        value = result.get("value", "") if result else ""
        return value
        
    except Exception as e:
        logger.error(f"Ошибка получения CRM текста {page}.{key}.{lang}: {e}")
        return ""


def get_current_user_dependency(request: Request) -> Dict[str, Any]:
    """Зависимость для получения текущего пользователя"""
    return get_current_user(request)


def get_all_images_for_template(lang: str = get_default_language()) -> Dict[str, str]:
    """
    Получить все переменные изображений для шаблона
    
    Args:
        lang: язык для alt-текстов
    
    Returns:
        Словарь с переменными изображений
    """
    try:
        # Получаем изображения с alt-текстами
        logo = query_one(
            """SELECT i.path, ia.alt_text 
               FROM images i 
               LEFT JOIN images_alts ia ON i.id = ia.image_id AND ia.lang = ?
               WHERE i.type = 'logo' 
               ORDER BY i."order" LIMIT 1""",
            (lang,)
        )
        
        background = query_one(
            """SELECT i.path, ia.alt_text 
               FROM images i 
               LEFT JOIN images_alts ia ON i.id = ia.image_id AND ia.lang = ?
               WHERE i.type = 'background' 
               ORDER BY i."order" LIMIT 1""",
            (lang,)
        )
        
        favicon = query_one(
            """SELECT i.path, ia.alt_text 
               FROM images i 
               LEFT JOIN images_alts ia ON i.id = ia.image_id AND ia.lang = ?
               WHERE i.type = 'favicon' 
               ORDER BY i."order" LIMIT 1""",
            (lang,)
        )
        
        # Получаем слайдер изображения
        slider_images = query_all(
            """SELECT i.path, ia.alt_text, i."order"
               FROM images i 
               LEFT JOIN images_alts ia ON i.id = ia.image_id AND ia.lang = ?
               WHERE i.type = 'slider' 
               ORDER BY i."order" LIMIT 4""",
            (lang,)
        )
        
        # Формируем словарь переменных
        images = {}
        
        # Основные изображения
        images["logo"] = logo.get("path", "") if logo else ""
        images["logo_alt"] = logo.get("alt_text", "") if logo else ""
        
        images["background"] = background.get("path", "") if background else ""
        images["background_alt"] = background.get("alt_text", "") if background else ""
        
        images["favicon"] = favicon.get("path", "") if favicon else ""
        images["favicon_alt"] = favicon.get("alt_text", "") if favicon else ""
        
        # Слайдер изображения
        for i, slider_img in enumerate(slider_images, 1):
            images[f"slider{i}"] = slider_img.get("path", "")
            images[f"slider{i}_alt"] = slider_img.get("alt_text", "")
        
        # Заполняем пустые слоты слайдера
        for i in range(len(slider_images) + 1, 5):
            images[f"slider{i}"] = ""
            images[f"slider{i}_alt"] = ""
        
        return images
        
    except Exception as e:
        logger.error(f"Ошибка получения переменных изображений: {e}")
        return {}


# Используем общие функции хеширования из app.auth.security


def get_dashboard_stats() -> Dict[str, Any]:
    """Получить статистику для Dashboard"""
    try:
        # Количество изображений
        images_count = query_one("SELECT COUNT(*) as count FROM images")["count"]
        
        # Количество активных языков (уникальные языки в таблице texts)
        languages = query_all("SELECT DISTINCT lang FROM texts")
        languages_count = len(languages)
        active_languages = [lang["lang"] for lang in languages]
        
        # Количество уникальных текстовых переменных из публичных шаблонов
        # Подсчитываем уникальные комбинации page+key из таблицы texts (публичные шаблоны)
        texts_count_result = query_one("SELECT COUNT(DISTINCT page || '.' || key) as count FROM texts")
        texts_count = texts_count_result["count"] if texts_count_result else 0
        
        # Количество пользователей
        users_count = query_one("SELECT COUNT(*) as count FROM users")["count"]
        
        return {
            "images_count": images_count,
            "languages_count": languages_count,
            "active_languages": active_languages,
            "texts_count": texts_count,
            "users_count": users_count
        }
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return {
            "images_count": 0,
            "languages_count": 0,
            "active_languages": [],
            "texts_count": 0,
            "users_count": 0
        }


def get_dashboard_translations(lang: str) -> Dict[str, str]:
    """Получить переводы для Dashboard"""
    translations = {}
    
    # Список ключей переводов для Dashboard
    translation_keys = [
        'title', 'welcome', 'logout', 'images', 'languages', 'texts', 'users',
        'quick_actions', 'edit_texts', 'content_management', 'upload_management',
        'seo_settings', 'meta_optimization', 'access_management', 
        'template_variables', 'variable_management'
    ]
    
    for key in translation_keys:
        translations[key] = get_crm_text('dashboard', key, lang)
    
    return translations


def get_cms_texts_translations(lang: str) -> Dict[str, str]:
    """Получить переводы для CMS Texts Editor"""
    translations = {}
    
    translation_keys = [
        'title', 'subtitle', 'back_to_dashboard', 'page', 'key', 'language', 'value',
        'actions', 'edit', 'delete', 'save', 'cancel', 'add_text', 'edit_text',
        'title_tag', 'description', 'cta_text', 'phone', 'address',
        'home', 'about', 'catalog', 'contacts', 'russian', 'english', 'ukrainian'
    ]
    
    for key in translation_keys:
        translations[key] = get_crm_text('cms_texts', key, lang)
    
    return translations


def get_cms_images_translations(lang: str) -> Dict[str, str]:
    """Получить переводы для CMS Images Manager"""
    translations = {}
    
    translation_keys = [
        'title', 'subtitle', 'back_to_dashboard', 'upload_image', 'image_type',
        'logo', 'slider', 'background', 'favicon', 'order', 'upload',
        'uploaded_images', 'name', 'type', 'size', 'date', 'actions',
        'view', 'download', 'delete', 'upload_images', 'select_type', 'image_file',
        'uploading', 'no_images', 'drag_to_reorder', 'unknown', 'file_too_large',
        'unsupported_format', 'load_error', 'select_file_and_type', 'upload_success', 
        'upload_error', 'confirm_delete', 'delete_success', 'delete_error', 'close'
    ]
    
    for key in translation_keys:
        translations[key] = get_crm_text('cms_images', key, lang)
    
    return translations


def get_cms_seo_translations(lang: str) -> Dict[str, str]:
    """Получить переводы для CMS SEO Manager"""
    translations = {}
    
    translation_keys = [
        'title', 'subtitle', 'back_to_dashboard', 'page', 'language',
        'title_tag', 'description', 'keywords', 'save', 'cancel',
        'add_seo', 'edit_seo', 'seo_settings', 'home', 'about', 'catalog', 'contacts', 
        'russian', 'english', 'ukrainian', 'title_placeholder', 'description_placeholder', 
        'keywords_placeholder', 'characters', 'saving', 'preview', 'google_preview', 
        'enter_title', 'enter_description', 'enter_keywords', 'html_code', 'load_error', 
        'save_success', 'save_error'
    ]
    
    for key in translation_keys:
        translations[key] = get_crm_text('cms_seo', key, lang)
    
    return translations


def get_cms_users_translations(lang: str) -> Dict[str, str]:
    """Получить переводы для CMS Users Manager"""
    translations = {}
    
    translation_keys = [
        'title', 'subtitle', 'back_to_dashboard', 'add_user', 'system_users',
        'email', 'role', 'created_date', 'actions', 'password', 'cancel', 'create',
        'reset_password', 'new_password', 'reset', 'user_created', 'create_error',
        'password_reset', 'reset_error', 'load_error', 'no_users', 'delete',
        'confirm_delete', 'user_deleted', 'delete_error'
    ]
    
    for key in translation_keys:
        translations[key] = get_crm_text('cms_users', key, lang)
    
    return translations


def get_cms_template_variables_translations(lang: str) -> Dict[str, str]:
    """Получить переводы для CMS Template Variables Manager"""
    translations = {}
    
    translation_keys = [
        'title', 'subtitle', 'back_to_dashboard', 'template_variables', 'management',
        'total_pages', 'total_variables', 'missing_variables', 'sync', 'analyze', 'refresh',
        'sync_variables', 'analyze_templates', 'refresh_data', 'sync_success', 'sync_error',
        'analysis_success', 'analysis_error', 'load_error', 'no_variables', 'no_templates',
        'database_variables', 'template_analysis', 'variables_in_db', 'template_analysis_results',
        'page', 'language', 'variables_count', 'languages_count', 'file', 'variables', 'issues',
        'problems', 'unclosed_tag', 'invalid_syntax', 'sync_completed', 'analysis_completed',
        'sync_loading', 'analysis_loading', 'sync_button', 'analyze_button', 'refresh_button',
        'sync_variables_desc', 'analyze_templates_desc', 'refresh_data_desc'
    ]
    
    for key in translation_keys:
        translations[key] = get_crm_text('cms_template_variables', key, lang)
    
    return translations


def get_cms_dynamic_images_translations(lang: str) -> Dict[str, str]:
    """Получить переводы для CMS Dynamic Images Manager"""
    translations = {}
    
    translation_keys = [
        'title', 'subtitle', 'back_to_dashboard', 'dynamic_images', 'management',
        'total_pages', 'total_variables', 'total_images', 'sync', 'refresh',
        'sync_images', 'refresh_data', 'sync_success', 'sync_error', 'load_error',
        'no_variables', 'no_images', 'image_variables', 'images_info', 'page',
        'variables_count', 'images_count', 'file', 'variables', 'sync_completed',
        'sync_loading', 'sync_button', 'refresh_button', 'sync_images_desc', 'refresh_data_desc'
    ]
    
    for key in translation_keys:
        translations[key] = get_crm_text('cms_dynamic_images', key, lang)
    
    return translations


def get_cms_dynamic_seo_translations(lang: str) -> Dict[str, str]:
    """Получить переводы для CMS Dynamic SEO Manager"""
    translations = {}
    
    translation_keys = [
        'title', 'subtitle', 'back_to_dashboard', 'dynamic_seo', 'management',
        'total_pages', 'total_variables', 'total_seo_entries', 'sync', 'refresh',
        'sync_seo', 'refresh_data', 'sync_success', 'sync_error', 'load_error',
        'no_variables', 'no_seo_data', 'seo_variables', 'seo_data', 'page',
        'variables_count', 'seo_entries_count', 'file', 'variables', 'sync_completed',
        'sync_loading', 'sync_button', 'refresh_button', 'sync_seo_desc', 'refresh_data_desc'
    ]
    
    for key in translation_keys:
        translations[key] = get_crm_text('cms_dynamic_seo', key, lang)
    
    return translations


@router.get("/")
async def dashboard(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Главная панель CMS"""
    try:
        stats = get_dashboard_stats()
        
        # Получаем информацию о пользователе
        user_email = current_user.get("email", "User")
        user_role = current_user.get("role", "editor")
        
        # Получаем язык и настройки мультиязычности
        lang = get_language_from_request(request)
        supported_languages = get_supported_languages_from_request(request)
        language_urls = get_language_urls_from_request(request)
        
        # Проверяем, что данные получены правильно
        if not language_urls:
            logger.error(f"Language URLs is empty or None for path: {request.url.path}")
            # Создаем пустой словарь как fallback
            language_urls = {}
        if not supported_languages:
            logger.error(f"Supported languages is empty or None for path: {request.url.path}")
            # Создаем список по умолчанию как fallback
            supported_languages = get_supported_languages()
        
        # Получаем переводы для Dashboard и Header
        translations = get_dashboard_translations(lang)
        
        return templates.TemplateResponse(
            "crm/dashboard.html",
            {
                "request": request,
                "user_email": user_email,
                "user_role": user_role,
                "stats": stats,
                "lang": lang,
                "supported_languages": supported_languages,
                "language_urls": language_urls,
                "t": translations,  # Передаем переводы в шаблон
                "get_cms_url": get_cms_url  # Функция для генерации URL
            }
        )
    except Exception as e:
        logger.error(f"Ошибка рендеринга Dashboard: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки панели управления")


@router.get("/texts")
async def texts_editor(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Редактор текстов (заглушка)"""
    # Получаем язык и настройки мультиязычности
    lang = get_language_from_request(request)
    supported_languages = get_supported_languages_from_request(request)
    language_urls = get_language_urls_from_request(request)
    
    # Получаем переводы для CMS Texts Editor и Header
    translations = get_cms_texts_translations(lang)
    
    return templates.TemplateResponse(
        "crm/texts.html",
        {
            "request": request,
            "user_email": current_user.get("email", "Пользователь"),
            "lang": lang,
            "supported_languages": supported_languages,
            "language_urls": language_urls,
            "t": translations,
            "get_cms_url": get_cms_url
        }
    )


@router.get("/images")
async def images_manager(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Управление изображениями"""
    # Получаем язык и настройки мультиязычности
    lang = get_language_from_request(request)
    supported_languages = get_supported_languages_from_request(request)
    language_urls = get_language_urls_from_request(request)
    
    # Получаем переводы для CMS Images Manager и Header
    translations = get_cms_images_translations(lang)
    
    # Получаем переменные изображений для шаблона
    images = get_all_images_for_template(lang)
    
    return templates.TemplateResponse(
        "crm/images.html",
        {
            "request": request,
            "user_email": current_user.get("email", "Пользователь"),
            "lang": lang,
            "supported_languages": supported_languages,
            "language_urls": language_urls,
            "t": translations,
            "images": images,
            "get_cms_url": get_cms_url
        }
    )


@router.get("/seo")
async def seo_manager(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """SEO-панель (заглушка)"""
    # Получаем язык и настройки мультиязычности
    lang = get_language_from_request(request)
    supported_languages = get_supported_languages_from_request(request)
    language_urls = get_language_urls_from_request(request)
    
    # Получаем переводы для CMS SEO Manager и Header
    translations = get_cms_seo_translations(lang)
    
    return templates.TemplateResponse(
        "crm/seo.html",
        {
            "request": request,
            "user_email": current_user.get("email", "Пользователь"),
            "lang": lang,
            "supported_languages": supported_languages,
            "language_urls": language_urls,
            "t": translations,
            "get_cms_url": get_cms_url
        }
    )




@router.get("/users")
async def users_manager(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Управление пользователями (только для admin)"""
    user_role = current_user.get("role", "editor")
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен. Требуется роль admin")
    
    lang = get_language_from_request(request)
    supported_languages = get_supported_languages_from_request(request)
    language_urls = get_language_urls_from_request(request)
    
    # Получаем переводы для CMS Users Manager и Header
    translations = get_cms_users_translations(lang)
    
    return templates.TemplateResponse(
        "crm/users.html",
        {
            "request": request,
            "user_email": current_user.get("email", "Пользователь"),
            "lang": lang,
            "supported_languages": supported_languages,
            "language_urls": language_urls,
            "t": translations,
            "get_cms_url": get_cms_url
        }
    )


@router.get("/template-variables")
async def template_variables_manager(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Управление переменными шаблонов"""
    # Получаем язык и настройки мультиязычности
    lang = get_language_from_request(request)
    supported_languages = get_supported_languages_from_request(request)
    language_urls = get_language_urls_from_request(request)
    
    # Получаем переводы для CMS Template Variables Manager и Header
    translations = get_cms_template_variables_translations(lang)
    
    return templates.TemplateResponse(
        "crm/template_variables.html",
        {
            "request": request,
            "user_email": current_user.get("email", "Пользователь"),
            "lang": lang,
            "supported_languages": supported_languages,
            "language_urls": language_urls,
            "t": translations,
            "get_cms_url": get_cms_url
        }
    )


# API для работы с текстами
@router.get("/api/translations")
async def get_translations(lang: str, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Получить переводы для указанного языка"""
    try:
        # Валидация языка
        valid_langs = get_supported_languages()
        
        if lang not in valid_langs:
            return {"success": False, "message": f"Недопустимый язык. Доступные: {', '.join(valid_langs)}"}
        
        # Получаем переводы для CMS Images Manager
        translations = get_cms_images_translations(lang)
        
        return {
            "success": True,
            "translations": translations,
            "lang": lang
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения переводов: {e}")
        return {"success": False, "message": "Ошибка получения переводов"}


@router.get("/api/texts")
async def get_texts(page: str, lang: str, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Получить тексты для указанной страницы и языка"""
    try:
        # Валидация параметров
        valid_pages = TemplateParser.get_available_pages()
        valid_langs = get_supported_languages()
        
        if page not in valid_pages:
            return {"success": False, "message": f"Недопустимая страница. Доступные: {', '.join(valid_pages)}"}
        
        if lang not in valid_langs:
            return {"success": False, "message": f"Недопустимый язык. Доступные: {', '.join(valid_langs)}"}
        
        # Проверяем кэш
        cached_texts = text_cache.get(page, lang)
        if cached_texts is not None:
            logger.debug(f"Cache hit for {page}:{lang}")
            return {
                "success": True,
                "texts": cached_texts,
                "page": page,
                "lang": lang,
                "cached": True
            }
        
        # Получаем из БД
        texts_query = """
            SELECT key, value 
            FROM texts_crm 
            WHERE page = ? AND lang = ?
        """
        results = query_all(texts_query, (page, lang))
        
        # Преобразуем в словарь
        texts = {}
        for row in results:
            texts[row["key"]] = row["value"]
        
        # Сохраняем в кэш
        text_cache.set(page, lang, texts)
        logger.debug(f"Cache set for {page}:{lang}")
        
        return {
            "success": True,
            "texts": texts,
            "page": page,
            "lang": lang,
            "cached": False
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения текстов: {e}")
        return {"success": False, "message": "Ошибка получения текстов"}


@router.post("/api/texts")
async def save_texts(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Сохранить тексты для указанной страницы и языка"""
    try:
        # Получаем данные из запроса
        data = await request.json()
        page = data.get("page")
        lang = data.get("lang")
        texts = data.get("texts", {})
        
        # Валидация параметров
        valid_pages = TemplateParser.get_available_pages()
        valid_langs = get_supported_languages()
        
        if not page or page not in valid_pages:
            return {"success": False, "message": f"Недопустимая страница. Доступные: {', '.join(valid_pages)}"}
        
        if not lang or lang not in valid_langs:
            return {"success": False, "message": f"Недопустимый язык. Доступные: {', '.join(valid_langs)}"}
        
        if not isinstance(texts, dict):
            return {"success": False, "message": "Тексты должны быть объектом"}
        
        # Валидация ключей текстов - используем динамические поля из парсера
        try:
            parser = TemplateParser()
            all_variables = parser.get_database_variables(page)
            
            if page in all_variables:
                # Получаем все ключи для данной страницы
                page_variables = all_variables[page]
                valid_keys = list(page_variables.keys())
                
                # Фильтруем только текстовые поля (не SEO)
                valid_text_keys = [key for key in valid_keys if not key.startswith('meta_')]
            else:
                # Fallback на старые ключи, если страница не найдена в парсере
                valid_text_keys = ["title", "subtitle", "description", "cta_text", "phone", "address"]
            
            # Валидация ключей
            for key in texts.keys():
                if key not in valid_text_keys:
                    return {"success": False, "message": f"Недопустимый ключ текста: {key}. Доступные: {', '.join(valid_text_keys)}"}
                    
        except Exception as e:
            logger.warning(f"Ошибка получения динамических ключей для {page}: {e}, используем fallback")
            # Fallback на старые ключи при ошибке
            valid_text_keys = ["title", "subtitle", "description", "cta_text", "phone", "address"]
            for key in texts.keys():
                if key not in valid_text_keys:
                    return {"success": False, "message": f"Недопустимый ключ текста: {key}. Доступные: {', '.join(valid_text_keys)}"}
        
        # Сохраняем каждый текст через UPSERT
        for key, value in texts.items():
            if value:  # Сохраняем только непустые значения
                # Проверяем, существует ли запись
                existing = query_one(
                    "SELECT id FROM texts_crm WHERE page = ? AND key = ? AND lang = ?",
                    (page, key, lang)
                )
                
                if existing:
                    # Обновляем существующую запись
                    execute(
                        "UPDATE texts_crm SET value = ? WHERE page = ? AND key = ? AND lang = ?",
                        (str(value), page, key, lang)
                    )
                else:
                    # Создаем новую запись
                    execute(
                        "INSERT INTO texts_crm (page, key, lang, value) VALUES (?, ?, ?, ?)",
                        (page, key, lang, str(value))
                    )
        
        # Удаляем пустые значения из БД
        for key in valid_keys:
            if key not in texts or not texts[key]:
                delete_query = "DELETE FROM texts_crm WHERE page = ? AND key = ? AND lang = ?"
                execute(delete_query, (page, key, lang))
        
        # Инвалидируем кэш для этой страницы и языка
        text_cache.invalidate(page, lang)
        logger.debug(f"Cache invalidated for {page}:{lang}")
        
        return {
            "success": True,
            "message": "Тексты успешно сохранены",
            "page": page,
            "lang": lang
        }
        
    except Exception as e:
        logger.error(f"Ошибка сохранения текстов: {e}")
        return {"success": False, "message": "Ошибка сохранения текстов"}


@router.get("/api/cache/stats")
async def get_cache_stats(current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Получить статистику кэша (для отладки)"""
    try:
        stats = text_cache.get_stats()
        return {
            "success": True,
            "cache_stats": stats
        }
    except Exception as e:
        logger.error(f"Ошибка получения статистики кэша: {e}")
        return {"success": False, "message": "Ошибка получения статистики кэша"}


@router.post("/api/cache/clear")
async def clear_cache(current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Очистить кэш (для отладки)"""
    try:
        text_cache.clear()
        logger.info("Cache cleared by user request")
        return {
            "success": True,
            "message": "Кэш очищен"
        }
    except Exception as e:
        logger.error(f"Ошибка очистки кэша: {e}")
        return {"success": False, "message": "Ошибка очистки кэша"}


# ===== API для работы с изображениями =====

@router.post("/api/images/upload-test")
async def upload_image_test(
    file: UploadFile = File(...),
    image_type: str = Form(...)
):
    """Тестовый endpoint для загрузки изображений без аутентификации"""
    try:
        logger.info(f"Тестовая загрузка: {file.filename}, тип: {image_type}")
        
        # Читаем содержимое файла
        file_content = await file.read()
        logger.info(f"Файл прочитан, размер: {len(file_content)} байт, MIME: {file.content_type}")
        
        return {
            "success": True,
            "message": "Тестовая загрузка успешна",
            "file_info": {
                "filename": file.filename,
                "size": len(file_content),
                "content_type": file.content_type,
                "image_type": image_type
            }
        }
        
    except Exception as e:
        logger.error(f"Ошибка тестовой загрузки: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Ошибка тестовой загрузки: {str(e)}"}
        )

@router.get("/api/images")
async def get_images(request: Request, user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Получить список всех изображений"""
    logger.info(f"🔍 API /api/images called by user: {user.get('email', 'unknown')}")
    
    try:
        logger.info("📊 Querying images from database")
        images = query_all("""
            SELECT id, name, path, original_path, type, "order"
            FROM images 
            ORDER BY type, "order"
        """)
        
        logger.info(f"✅ Found {len(images)} images in database")
        for img in images:
            logger.info(f"🖼️ Image: ID={img['id']}, Name={img['name']}, Type={img['type']}, Path={img['path']}")
        
        result = {
            "success": True,
            "images": images
        }
        
        logger.info(f"📤 Returning {len(images)} images to client")
        return result
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения списка изображений: {e}")
        return {"success": False, "message": "Ошибка получения списка изображений"}


@router.post("/api/images/upload")
async def upload_image(
    file: UploadFile = File(...),
    image_type: str = Form(...),
    user: Dict[str, Any] = Depends(get_current_user_dependency)
):
    """Загрузить и оптимизировать изображение"""
    try:
        logger.info(f"Начало загрузки изображения: {file.filename}, тип: {image_type}, пользователь: {user.get('email', 'unknown')}")
        
        # Проверяем, что файл и тип переданы
        if not file or not file.filename:
            logger.error("Файл не передан")
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Файл не передан"}
            )
        
        if not image_type:
            logger.error("Тип изображения не передан")
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Тип изображения не передан"}
            )
        
        # Проверка типа изображения (теперь динамическая)
        if not image_type or not image_type.strip():
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Тип изображения не может быть пустым"}
            )
        
        # Читаем содержимое файла
        file_content = await file.read()
        logger.info(f"Файл прочитан, размер: {len(file_content)} байт, MIME: {file.content_type}")
        
        # Валидация файла
        is_valid, error_message = validate_image_file(
            file_content, file.filename, file.content_type
        )
        logger.info(f"Результат валидации: {is_valid}, сообщение: {error_message}")
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": error_message}
            )
        
        # Генерируем уникальное имя файла
        unique_filename = generate_unique_filename(file.filename)
        
        # Пути для сохранения
        uploads_dir = "uploads"
        originals_dir = os.path.join(uploads_dir, "originals")
        optimized_dir = os.path.join(uploads_dir, "optimized")
        
        original_path = os.path.join(originals_dir, unique_filename)
        optimized_path = os.path.join(optimized_dir, unique_filename.replace(os.path.splitext(unique_filename)[1], '.webp'))
        
        # Сохраняем оригинальное изображение
        if not save_original_image(file_content, original_path):
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": "Ошибка сохранения оригинального изображения"}
            )
        
        # Оптимизируем изображение
        if not optimize_image(file_content, optimized_path):
            # Удаляем оригинал если оптимизация не удалась
            try:
                os.remove(original_path)
            except:
                pass
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": "Ошибка оптимизации изображения"}
            )
        
        # Получаем информацию об изображении
        image_info = get_image_info(file_content)
        
        # Получаем следующий порядок для данного типа
        next_order = query_one(
            "SELECT COALESCE(MAX(\"order\"), 0) + 1 as next_order FROM images WHERE type = ?",
            (image_type,)
        )["next_order"]
        
        # Сохраняем информацию в БД (только имена файлов, без полных путей)
        execute("""
            INSERT INTO images (name, path, original_path, type, "order")
            VALUES (?, ?, ?, ?, ?)
        """, (unique_filename, os.path.join("optimized", unique_filename.replace(os.path.splitext(unique_filename)[1], '.webp')), os.path.join("originals", unique_filename), image_type, next_order))
        
        # Получаем ID созданной записи
        image_id = query_one("SELECT last_insert_rowid() as id")["id"]
        
        # Инвалидируем кэш изображений для данного типа
        image_cache.invalidate_type(image_type)
        
        logger.info(f"Изображение загружено: {unique_filename}, тип: {image_type}")
        
        return {
            "success": True,
            "message": "Изображение успешно загружено",
            "image": {
                "id": image_id,
                "name": unique_filename,
                "path": optimized_path,
                "original_path": original_path,
                "type": image_type,
                "order": next_order,
                "info": image_info
            }
        }
        
    except Exception as e:
        logger.error(f"Ошибка загрузки изображения: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Ошибка загрузки изображения: {str(e)}"}
        )


@router.delete("/api/images/{image_id}")
async def delete_image(
    image_id: int,
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user_dependency)
):
    """Удалить изображение"""
    try:
        # Получаем информацию об изображении
        image = query_one("SELECT * FROM images WHERE id = ?", (image_id,))
        if not image:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Изображение не найдено"}
            )
        
        # Удаляем файлы
        try:
            if os.path.exists(image["path"]):
                os.remove(image["path"])
            if os.path.exists(image["original_path"]):
                os.remove(image["original_path"])
        except Exception as e:
            logger.warning(f"Ошибка удаления файлов изображения {image_id}: {e}")
        
        # Удаляем запись из БД
        execute("DELETE FROM images WHERE id = ?", (image_id,))
        
        # Инвалидируем кэш изображений для данного типа
        image_cache.invalidate_type(image["type"])
        
        logger.info(f"Изображение удалено: {image['name']}")
        
        return {
            "success": True,
            "message": "Изображение успешно удалено"
        }
        
    except Exception as e:
        logger.error(f"Ошибка удаления изображения: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Ошибка удаления изображения"}
        )


@router.post("/api/images/update")
async def update_existing_image(
    file: UploadFile = File(...),
    image_id: int = Form(...),
    user: Dict[str, Any] = Depends(get_current_user_dependency)
):
    """Обновить существующее изображение"""
    try:
        logger.info(f"Обновление изображения ID {image_id}: {file.filename}")
        
        # Проверяем существование изображения
        image = query_one("SELECT * FROM images WHERE id = ?", (image_id,))
        if not image:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Изображение не найдено"}
            )
        
        # Проверяем файл
        if not file or not file.filename:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Файл не передан"}
            )
        
        # Проверяем размер файла (5MB)
        if file.size and file.size > 5 * 1024 * 1024:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Файл слишком большой (максимум 5MB)"}
            )
        
        # Проверяем тип файла
        if not file.content_type or not file.content_type.startswith('image/'):
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Неподдерживаемый формат файла"}
            )
        
        # Читаем содержимое файла
        file_content = await file.read()
        
        # Генерируем уникальное имя файла
        # Всегда используем .webp расширение для оптимизированных файлов
        unique_filename = f"{uuid.uuid4()}.webp"
        
        # Пути для сохранения
        uploads_dir = Path("uploads")
        originals_dir = uploads_dir / "originals"
        optimized_dir = uploads_dir / "optimized"
        
        # Создаем директории если не существуют
        originals_dir.mkdir(parents=True, exist_ok=True)
        optimized_dir.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем оригинальный файл (с оригинальным расширением)
        original_extension = file.filename.split('.')[-1].lower()
        original_filename = f"{uuid.uuid4()}.{original_extension}"
        original_path = originals_dir / original_filename
        with open(original_path, "wb") as f:
            f.write(file_content)
        
        # Оптимизируем изображение (всегда в .webp)
        optimized_path = optimized_dir / unique_filename
        optimize_image(file_content, str(optimized_path))
        
        # Обновляем запись в БД
        execute(
            "UPDATE images SET name = ?, path = ?, original_path = ? WHERE id = ?",
            (file.filename, unique_filename, original_filename, image_id)
        )
        
        logger.info(f"Изображение {image_id} обновлено: {unique_filename}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True, 
                "message": "Изображение обновлено",
                "image": {
                    "id": image_id,
                    "name": file.filename,
                    "path": unique_filename,
                    "original_path": unique_filename
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Ошибка обновления изображения {image_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Ошибка обновления изображения"}
        )


@router.post("/api/images/{image_id}/update")
async def update_image_record(
    image_id: int,
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user_dependency)
):
    """Обновить запись изображения в БД"""
    try:
        # Проверяем существование изображения
        image = query_one("SELECT * FROM images WHERE id = ?", (image_id,))
        if not image:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Изображение не найдено"}
            )
        
        # Обновляем запись изображения (пока просто обновляем timestamp)
        execute(
            "UPDATE images SET created_at = datetime('now') WHERE id = ?",
            (image_id,)
        )
        
        logger.info(f"Обновлена запись изображения {image_id}")
        
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Запись изображения обновлена"}
        )
        
    except Exception as e:
        logger.error(f"Ошибка обновления записи изображения {image_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Ошибка обновления записи изображения"}
        )


@router.put("/api/images/{image_id}/order")
async def update_image_order(
    image_id: int,
    request: Request,
    new_order: int = Form(...),
    user: Dict[str, Any] = Depends(get_current_user_dependency)
):
    """Обновить порядок изображения"""
    try:
        # Проверяем существование изображения
        image = query_one("SELECT * FROM images WHERE id = ?", (image_id,))
        if not image:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Изображение не найдено"}
            )
        
        # Обновляем порядок
        execute("UPDATE images SET \"order\" = ? WHERE id = ?", (new_order, image_id))
        
        logger.info(f"Порядок изображения {image_id} обновлен на {new_order}")
        
        return {
            "success": True,
            "message": "Порядок изображения обновлен"
        }
        
    except Exception as e:
        logger.error(f"Ошибка обновления порядка изображения: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Ошибка обновления порядка изображения"}
        )


@router.get("/api/images/by-type/{image_type}")
async def get_images_by_type(
    image_type: str,
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user_dependency)
):
    """Получить изображения по типу"""
    try:
        # Проверка типа изображения (теперь динамическая)
        if not image_type or not image_type.strip():
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Тип изображения не может быть пустым"}
            )
        
        images = query_all("""
            SELECT id, name, path, original_path, type, "order"
            FROM images 
            WHERE type = ? 
            ORDER BY "order"
        """, (image_type,))
        
        return {
            "success": True,
            "images": images
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения изображений по типу: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Ошибка получения изображений по типу"}
        )


@router.get("/api/images/{image_id}/alts")
async def get_image_alts(
    image_id: int,
    user: Dict[str, Any] = Depends(get_current_user_dependency)
):
    """Получить alt-тексты для изображения"""
    try:
        alts = query_all("""
            SELECT lang, alt_text 
            FROM images_alts 
            WHERE image_id = ?
            ORDER BY lang
        """, (image_id,))
        
        return {
            "success": True,
            "alts": {alt["lang"]: alt["alt_text"] for alt in alts}
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения alt-текстов: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Ошибка получения alt-текстов"}
        )


@router.post("/api/images/{image_id}/alts")
async def save_image_alts(
    image_id: int,
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user_dependency)
):
    """Сохранить alt-тексты для изображения"""
    try:
        data = await request.json()
        alts = data.get("alts", {})
        
        # Удаляем существующие alt-тексты
        execute("DELETE FROM images_alts WHERE image_id = ?", (image_id,))
        
        # Добавляем новые alt-тексты
        for lang, alt_text in alts.items():
            if alt_text.strip():  # Только непустые alt-тексты
                execute(
                    "INSERT INTO images_alts (image_id, lang, alt_text) VALUES (?, ?, ?)",
                    (image_id, lang, alt_text.strip())
                )
        
        # Инвалидируем кэш изображений
        image_cache.clear()
        
        return {
            "success": True,
            "message": "Alt-тексты сохранены"
        }
        
    except Exception as e:
        logger.error(f"Ошибка сохранения alt-текстов: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Ошибка сохранения alt-текстов"}
        )


# ===== API для работы с SEO =====

@router.get("/api/seo")
async def get_seo(page: str, lang: str, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Получить SEO данные для указанной страницы и языка"""
    try:
        # Валидация параметров
        valid_pages = TemplateParser.get_available_pages()
        valid_langs = get_supported_languages()
        
        if page not in valid_pages:
            return {"success": False, "message": f"Недопустимая страница. Доступные: {', '.join(valid_pages)}"}
        
        if lang not in valid_langs:
            return {"success": False, "message": f"Недопустимый язык. Доступные: {', '.join(valid_langs)}"}
        
        # Получаем SEO данные из БД
        seo_query = """
            SELECT title, description, keywords 
            FROM seo 
            WHERE page = ? AND lang = ?
        """
        seo_data = query_one(seo_query, (page, lang))
        
        # Если данных нет, возвращаем пустые значения
        if not seo_data:
            seo_data = {
                "title": "",
                "description": "",
                "keywords": ""
            }
        
        return {
            "success": True,
            "seo": seo_data,
            "page": page,
            "lang": lang
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения SEO данных: {e}")
        return {"success": False, "message": "Ошибка получения SEO данных"}


@router.post("/api/seo")
async def save_seo(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Сохранить SEO данные для указанной страницы и языка"""
    try:
        # Получаем данные из запроса
        data = await request.json()
        page = data.get("page")
        lang = data.get("lang")
        seo_data = data.get("seo", {})
        
        # Валидация параметров
        valid_pages = TemplateParser.get_available_pages()
        valid_langs = get_supported_languages()
        
        if not page or page not in valid_pages:
            return {"success": False, "message": f"Недопустимая страница. Доступные: {', '.join(valid_pages)}"}
        
        if not lang or lang not in valid_langs:
            return {"success": False, "message": f"Недопустимый язык. Доступные: {', '.join(valid_langs)}"}
        
        if not isinstance(seo_data, dict):
            return {"success": False, "message": "SEO данные должны быть объектом"}
        
        # Валидация длин полей
        title = seo_data.get("title", "")
        description = seo_data.get("description", "")
        keywords = seo_data.get("keywords", "")
        
        # Валидация длин (рекомендации SEO)
        if title and len(title) > 60:
            return {"success": False, "message": "Title не должен превышать 60 символов"}
        
        if description and len(description) > 160:
            return {"success": False, "message": "Description не должен превышать 160 символов"}
        
        if keywords and len(keywords) > 255:
            return {"success": False, "message": "Keywords не должны превышать 255 символов"}
        
        # Проверяем, существует ли запись
        existing = query_one(
            "SELECT id FROM seo WHERE page = ? AND lang = ?",
            (page, lang)
        )
        
        if existing:
            # Обновляем существующую запись
            execute("""
                UPDATE seo 
                SET title = ?, description = ?, keywords = ?
                WHERE page = ? AND lang = ?
            """, (title, description, keywords, page, lang))
        else:
            # Создаем новую запись
            execute("""
                INSERT INTO seo (page, lang, title, description, keywords)
                VALUES (?, ?, ?, ?, ?)
            """, (page, lang, title, description, keywords))
        
        logger.info(f"SEO данные сохранены для {page}:{lang}")
        
        return {
            "success": True,
            "message": "SEO данные успешно сохранены",
            "page": page,
            "lang": lang
        }
        
    except Exception as e:
        logger.error(f"Ошибка сохранения SEO данных: {e}")
        return {"success": False, "message": "Ошибка сохранения SEO данных"}




# ==================== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ====================

@router.get("/api/users")
async def get_users(current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Получить список всех пользователей (только для admin)"""
    try:
        # Проверяем роль пользователя
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        # Получаем список пользователей
        users = query_all("""
            SELECT id, email, role, created_at 
            FROM users 
            ORDER BY created_at DESC
        """)
        
        return {
            "success": True,
            "users": users
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения списка пользователей: {e}")
        return {"success": False, "message": "Ошибка получения списка пользователей"}


@router.post("/api/users")
async def create_user(
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    current_user: Dict[str, Any] = Depends(get_current_user_dependency)
):
    """Создать нового пользователя (только для admin)"""
    try:
        # Проверяем роль пользователя
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        # Валидация данных
        if not email or len(email) < 5:
            return {"success": False, "message": "Некорректный email"}
        
        if not password or len(password) < 8:
            return {"success": False, "message": "Пароль должен содержать минимум 8 символов"}
        
        if len(password.encode('utf-8')) > 72:
            return {"success": False, "message": "Пароль не может быть длиннее 72 байтов"}
        
        if role not in ["admin", "editor"]:
            return {"success": False, "message": "Некорректная роль"}
        
        # Проверяем, что пользователь с таким email не существует
        existing_user = query_one("SELECT id FROM users WHERE email = ?", (email,))
        if existing_user:
            return {"success": False, "message": "Пользователь с таким email уже существует"}
        
        # Хэшируем пароль с помощью bcrypt
        password_hash = hash_password(password)
        
        # Создаем пользователя
        execute("""
            INSERT INTO users (email, password_hash, role, created_at)
            VALUES (?, ?, ?, datetime('now'))
        """, (email, password_hash, role))
        
        return {"success": True, "message": "Пользователь успешно создан"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка создания пользователя: {e}")
        return {"success": False, "message": "Ошибка создания пользователя"}


@router.delete("/api/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user_dependency)
):
    """Удалить пользователя (только для admin)"""
    try:
        # Проверяем роль пользователя
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        # Проверяем, что пользователь существует
        user = query_one("SELECT id, email FROM users WHERE id = ?", (user_id,))
        if not user:
            return {"success": False, "message": "Пользователь не найден"}
        
        # Нельзя удалить самого себя
        if user_id == current_user.get("id"):
            return {"success": False, "message": "Нельзя удалить самого себя"}
        
        # Удаляем пользователя
        execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        return {"success": True, "message": "Пользователь успешно удален"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления пользователя: {e}")
        return {"success": False, "message": "Ошибка удаления пользователя"}


@router.post("/api/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    new_password: str = Form(...),
    current_user: Dict[str, Any] = Depends(get_current_user_dependency)
):
    """Сбросить пароль пользователя (только для admin)"""
    try:
        # Проверяем роль пользователя
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        # Валидация пароля
        if not new_password or len(new_password) < 8:
            return {"success": False, "message": "Пароль должен содержать минимум 8 символов"}
        
        if len(new_password.encode('utf-8')) > 72:
            return {"success": False, "message": "Пароль не может быть длиннее 72 байтов"}
        
        # Проверяем, что пользователь существует
        user = query_one("SELECT id, email FROM users WHERE id = ?", (user_id,))
        if not user:
            return {"success": False, "message": "Пользователь не найден"}
        
        # Хэшируем новый пароль с помощью bcrypt
        password_hash = hash_password(new_password)
        
        # Обновляем пароль
        execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
        
        return {"success": True, "message": "Пароль успешно сброшен"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка сброса пароля: {e}")
        return {"success": False, "message": "Ошибка сброса пароля"}


@router.get("/api/session-check")
async def check_session(request: Request):
    """Проверить статус сессии и время до истечения"""
    try:
        # Получаем токен из cookies
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=401, detail="No session token")
        
        # Декодируем токен
        payload = decode_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid session token")
        
        # Проверяем истечение
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            current_time = datetime.now(timezone.utc).timestamp()
            if current_time >= exp_timestamp:
                raise HTTPException(status_code=401, detail="Session expired")
            
            # Возвращаем информацию о сессии
            expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            time_until_expiry = exp_timestamp - current_time
            
            return {
                "valid": True,
                "expires_at": expires_at.isoformat(),
                "time_until_expiry_seconds": int(time_until_expiry),
                "user_id": payload.get("sub"),
                "role": payload.get("role")
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid session token")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session check error: {e}")
        raise HTTPException(status_code=500, detail="Session check failed")


@router.post("/api/session-refresh")
async def refresh_session(request: Request, response: JSONResponse):
    """Обновить сессию (продлить JWT токен)"""
    try:
        # Получаем текущего пользователя
        user = get_current_user(request)
        
        # Создаем новый токен
        new_token = create_access_token(
            subject=str(user["id"]), 
            role=user["role"]
        )
        
        # Устанавливаем новый cookie
        set_secure_cookie(
            response=response,
            key="access_token",
            value=new_token,
            max_age=int(os.getenv("JWT_EXPIRES_MINUTES", "15")) * 60,
            httponly=True,
            samesite="lax"
        )
        
        return {"success": True, "message": "Session refreshed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session refresh error: {e}")
        raise HTTPException(status_code=500, detail="Session refresh failed")


# ===== СТРАНИЦА УПРАВЛЕНИЯ ПЕРЕМЕННЫМИ ШАБЛОНОВ =====

@router.get("/template-variables")
async def template_variables_page(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Страница управления переменными шаблонов"""
    try:
        lang = get_language_from_request(request)
        language_urls = get_language_urls_from_request(request)
        supported_languages = get_supported_languages_from_request(request)
        
        return templates.TemplateResponse("crm/template_variables.html", {
            "request": request,
            "current_user": current_user,
            "lang": lang,
            "language_urls": language_urls,
            "supported_languages": supported_languages,
            "cms_url": get_cms_url("", lang),
            "cms_dashboard_url": get_cms_url("", lang)
        })
        
    except Exception as e:
        logger.error(f"Ошибка загрузки страницы переменных шаблонов: {e}")
        raise HTTPException(status_code=500, detail="Failed to load template variables page")


# ===== API ENDPOINTS ДЛЯ УПРАВЛЕНИЯ ПЕРЕМЕННЫМИ ШАБЛОНОВ =====

@router.get("/api/template-variables")
async def get_template_variables(request: Request, page: str = None):
    """Получить все переменные шаблонов из базы данных"""
    try:
        parser = TemplateParser()
        variables = parser.get_database_variables(page)
        
        return {
            "success": True,
            "variables": variables,
            "total_pages": len(variables),
            "total_variables": sum(len(page_vars) for page_vars in variables.values())
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения переменных шаблонов: {e}")
        raise HTTPException(status_code=500, detail="Failed to get template variables")


@router.get("/api/dynamic-fields")
async def get_dynamic_fields(request: Request, page: str, lang: str, field_type: str = "texts"):
    """Получить динамические поля для указанной страницы, языка и типа"""
    try:
        parser = TemplateParser()
        
        # Получаем все переменные для страницы
        all_variables = parser.get_database_variables(page)
        
        if page not in all_variables:
            return {
                "success": True,
                "fields": [],
                "message": f"Переменные для страницы {page} не найдены"
            }
        
        # Фильтруем по типу поля (texts, seo)
        page_variables = all_variables[page]
        filtered_fields = {}
        
        for key, lang_data in page_variables.items():
            if field_type == "texts" and not key.startswith("meta_"):
                # Для текстовых полей исключаем SEO поля
                filtered_fields[key] = lang_data.get(lang, "")
            elif field_type == "seo" and key.startswith("meta_"):
                # Для SEO полей берем только meta_ поля
                filtered_fields[key] = lang_data.get(lang, "")
        
        # Преобразуем в список полей для формы
        fields = []
        for key, value in filtered_fields.items():
            field_info = {
                "key": key,
                "value": value,
                "label": _get_field_label(key),
                "type": _get_field_type(key),
                "placeholder": _get_field_placeholder(key),
                "required": _is_field_required(key)
            }
            fields.append(field_info)
        
        return {
            "success": True,
            "fields": fields,
            "page": page,
            "lang": lang,
            "field_type": field_type
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения динамических полей: {e}")
        return {"success": False, "message": f"Ошибка получения полей: {e}"}


def _get_field_label(key: str) -> str:
    """Получить человекочитаемый лейбл для поля"""
    labels = {
        "title": "Заголовок",
        "subtitle": "Подзаголовок", 
        "description": "Описание",
        "cta_text": "Текст кнопки",
        "phone": "Телефон",
        "address": "Адрес",
        "email": "Email",
        "meta_title": "SEO заголовок",
        "meta_description": "SEO описание",
        "meta_keywords": "SEO ключевые слова"
    }
    return labels.get(key, key.replace("_", " ").title())


def _get_field_type(key: str) -> str:
    """Определить тип поля"""
    if key in ["description", "address"]:
        return "textarea"
    elif key.startswith("meta_"):
        return "text"
    else:
        return "text"


def _get_field_placeholder(key: str) -> str:
    """Получить placeholder для поля"""
    placeholders = {
        "title": "Введите заголовок",
        "subtitle": "Введите подзаголовок",
        "description": "Введите описание",
        "cta_text": "Введите текст кнопки",
        "phone": "Введите номер телефона",
        "address": "Введите адрес",
        "email": "Введите email",
        "meta_title": "SEO заголовок (до 60 символов)",
        "meta_description": "SEO описание (до 160 символов)",
        "meta_keywords": "Ключевые слова через запятую"
    }
    return placeholders.get(key, f"Введите {key}")


def _is_field_required(key: str) -> bool:
    """Определить обязательность поля"""
    required_fields = ["title"]
    return key in required_fields


@router.get("/api/image-types")
async def get_image_types(request: Request, page: str = None):
    """Получить типы изображений, используемые в шаблонах"""
    try:
        from app.utils.template_parser import TemplateParser
        
        parser = TemplateParser()
        
        # Получаем все переменные для страницы или всех страниц
        if page:
            all_variables = parser.get_database_variables(page)
            if page not in all_variables:
                return {
                    "success": True,
                    "image_types": [],
                    "message": f"Переменные для страницы {page} не найдены"
                }
            page_variables = {page: all_variables[page]}
        else:
            page_variables = parser.get_database_variables()
        
        # Ищем переменные изображений
        image_types = set()
        for page_name, variables in page_variables.items():
            for key, lang_data in variables.items():
                if key.startswith("image_") or key in ["logo", "background", "favicon", "slider"]:
                    # Извлекаем тип изображения
                    if key.startswith("image_"):
                        image_type = key.replace("image_", "")
                    else:
                        image_type = key
                    image_types.add(image_type)
        
        # Преобразуем в список с метаданными
        image_types_list = []
        for img_type in sorted(image_types):
            metadata = {
                "type": img_type,
                "label": _get_image_type_label(img_type),
                "description": _get_image_type_description(img_type),
                "max_files": _get_max_files_for_type(img_type)
            }
            image_types_list.append(metadata)
        
        return {
            "success": True,
            "image_types": image_types_list,
            "page": page
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения типов изображений: {e}")
        return {"success": False, "message": f"Ошибка получения типов изображений: {e}"}


def _get_image_type_label(img_type: str) -> str:
    """Получить человекочитаемый лейбл для типа изображения"""
    labels = {
        "logo": "Логотип",
        "slider": "Слайдер",
        "background": "Фоновое изображение",
        "favicon": "Иконка сайта",
        "banner": "Баннер",
        "gallery": "Галерея"
    }
    return labels.get(img_type, img_type.replace("_", " ").title())


def _get_image_type_description(img_type: str) -> str:
    """Получить описание для типа изображения"""
    descriptions = {
        "logo": "Логотип компании, отображается в шапке сайта",
        "slider": "Изображения для слайдера на главной странице",
        "background": "Фоновые изображения для секций",
        "favicon": "Иконка сайта, отображается во вкладке браузера",
        "banner": "Рекламные баннеры",
        "gallery": "Изображения для галереи"
    }
    return descriptions.get(img_type, f"Изображения типа {img_type}")


def _get_max_files_for_type(img_type: str) -> int:
    """Получить максимальное количество файлов для типа"""
    limits = {
        "logo": 1,
        "favicon": 1,
        "background": 3,
        "slider": 10,
        "banner": 5,
        "gallery": 20
    }
    return limits.get(img_type, 5)


@router.post("/api/sync-template-variables")
async def sync_template_variables(request: Request):
    """Синхронизировать переменные шаблонов с базой данных"""
    try:
        from app.utils.template_parser import TemplateParser
        from app.site.config import get_supported_languages
        
        parser = TemplateParser()
        supported_languages = get_supported_languages()
        results = parser.sync_variables_to_database(supported_languages)
        
        return {
            "success": True,
            "message": "Template variables synchronized successfully",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Ошибка синхронизации переменных шаблонов: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync template variables")


@router.get("/api/missing-variables")
async def get_missing_variables(request: Request):
    """Получить переменные, которые есть в шаблонах, но отсутствуют в БД"""
    try:
        parser = TemplateParser()
        supported_languages = get_supported_languages()
        missing = parser.get_missing_variables(supported_languages)
        
        return {
            "success": True,
            "missing_variables": missing,
            "total_missing": sum(len(vars) for vars in missing.values())
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения отсутствующих переменных: {e}")
        raise HTTPException(status_code=500, detail="Failed to get missing variables")


@router.get("/api/template-analysis")
async def get_template_analysis(request: Request):
    """Получить анализ шаблонов - найденные переменные, проблемы синтаксиса"""
    try:
        from app.utils.template_parser import TemplateParser
        
        parser = TemplateParser()
        
        # Парсим все шаблоны
        template_variables = parser.parse_all_templates()
        
        # Анализируем каждый шаблон
        analysis = {}
        public_templates = Path("app/templates/public")
        
        if public_templates.exists():
            for template_file in public_templates.glob("*.html"):
                page = parser.get_page_from_path(str(template_file))
                variables = parser.extract_variables_from_file(str(template_file))
                syntax_issues = parser.validate_template_syntax(str(template_file))
                
                analysis[page] = {
                    "file": str(template_file),
                    "variables": list(variables),
                    "syntax_issues": syntax_issues,
                    "has_issues": bool(syntax_issues['unclosed_tags'] or syntax_issues['invalid_syntax'])
                }
        
        return {
            "success": True,
            "analysis": analysis,
            "total_templates": len(analysis),
            "total_variables": sum(len(data['variables']) for data in analysis.values())
        }
        
    except Exception as e:
        logger.error(f"Ошибка анализа шаблонов: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze templates")


# ===== API для работы с переводами =====

@router.get("/api/translations")
async def get_translations(
    module: str, 
    lang: str = None,
    request: Request = None,
    current_user: Dict[str, Any] = Depends(get_current_user_dependency)
):
    """Получить переводы для указанного модуля и языка"""
    try:
        # Если язык не указан, получаем из запроса
        if not lang:
            lang = get_language_from_request(request)
        
        # Валидация модулей
        valid_modules = ["cms_users", "cms_texts", "cms_images", "cms_seo", "cms_template_variables", "header"]
        if module not in valid_modules:
            return {"success": False, "message": f"Недопустимый модуль. Доступные: {', '.join(valid_modules)}"}
        
        # Получаем переводы для модуля
        if module == "cms_users":
            translations = get_cms_users_translations(lang)
        elif module == "cms_texts":
            translations = get_cms_texts_translations(lang)
        elif module == "cms_images":
            translations = get_cms_images_translations(lang)
        elif module == "cms_seo":
            translations = get_cms_seo_translations(lang)
        elif module == "cms_template_variables":
            translations = get_cms_template_variables_translations(lang)
        
        return {
            "success": True,
            "translations": translations,
            "module": module,
            "lang": lang
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения переводов: {e}")
        return {"success": False, "message": "Ошибка получения переводов"}


