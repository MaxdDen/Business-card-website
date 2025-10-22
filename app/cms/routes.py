from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, RedirectResponse
from app.auth.security import get_current_user
from app.database.db import query_one, query_all, execute
from app.utils.cache import text_cache, image_cache, invalidate_content_caches
from app.site.middleware import get_language_from_request, get_supported_languages_from_request, get_language_urls_from_request
from app.site.config import get_default_language
from app.site.routes import get_text
from app.utils.images import (
    validate_image_file, optimize_image, save_original_image, 
    generate_unique_filename, get_image_info
)
from typing import Dict, Any, List
import logging
import json
import os
import io

router = APIRouter(prefix="/cms", tags=["cms"])
templates = Jinja2Templates(directory="app/templates")

logger = logging.getLogger(__name__)


def get_current_user_dependency(request: Request) -> Dict[str, Any]:
    """Зависимость для получения текущего пользователя"""
    return get_current_user(request)


def safe_hash_password(password: str) -> str:
    """
    Безопасное хэширование пароля с учетом ограничений bcrypt
    
    Args:
        password: Пароль для хэширования
        
    Returns:
        Хэшированный пароль
        
    Raises:
        Exception: Если не удается хэшировать пароль
    """
    import bcrypt
    
    # Обрезаем пароль до 72 байтов для совместимости с bcrypt
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Генерируем соль и хэшируем пароль
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt)
    
    return password_hash.decode('utf-8')


def get_dashboard_stats() -> Dict[str, Any]:
    """Получить статистику для Dashboard"""
    try:
        # Количество изображений
        images_count = query_one("SELECT COUNT(*) as count FROM images")["count"]
        
        # Количество активных языков (уникальные языки в таблице texts)
        languages = query_all("SELECT DISTINCT lang FROM texts")
        languages_count = len(languages)
        active_languages = [lang["lang"] for lang in languages]
        
        # Количество текстовых блоков
        texts_count = query_one("SELECT COUNT(*) as count FROM texts")["count"]
        
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
        'seo_settings', 'meta_optimization', 'access_management'
    ]
    
    for key in translation_keys:
        translations[key] = get_text('dashboard', key, lang)
    
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
        translations[key] = get_text('cms_texts', key, lang)
    
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
        translations[key] = get_text('cms_images', key, lang)
    
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
        translations[key] = get_text('cms_seo', key, lang)
    
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
        translations[key] = get_text('cms_users', key, lang)
    
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
            supported_languages = ["en", "ru", "ua"]
        
        # Отладочная информация
        logger.info(f"Dashboard Debug - Path: {request.url.path}, Lang: {lang}")
        logger.info(f"Dashboard Debug - Supported languages: {supported_languages}")
        logger.info(f"Dashboard Debug - Language URLs: {language_urls}")
        logger.info(f"Dashboard Debug - Language URLs type: {type(language_urls)}")
        logger.info(f"Dashboard Debug - Language URLs length: {len(language_urls) if language_urls else 'None'}")
        
        # Получаем переводы для Dashboard
        translations = get_dashboard_translations(lang)
        
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user_email": user_email,
                "user_role": user_role,
                "stats": stats,
                "lang": lang,
                "supported_languages": supported_languages,
                "language_urls": language_urls,
                "t": translations  # Передаем переводы в шаблон
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
    
    # Получаем переводы для CMS Texts Editor
    translations = get_cms_texts_translations(lang)
    
    return templates.TemplateResponse(
        "texts.html",
        {
            "request": request,
            "user_email": current_user.get("email", "Пользователь"),
            "lang": lang,
            "supported_languages": supported_languages,
            "language_urls": language_urls,
            "t": translations
        }
    )


@router.get("/images")
async def images_manager(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Управление изображениями (заглушка)"""
    # Получаем язык и настройки мультиязычности
    lang = get_language_from_request(request)
    supported_languages = get_supported_languages_from_request(request)
    language_urls = get_language_urls_from_request(request)
    
    # Получаем переводы для CMS Images Manager
    translations = get_cms_images_translations(lang)
    
    return templates.TemplateResponse(
        "images.html",
        {
            "request": request,
            "user_email": current_user.get("email", "Пользователь"),
            "lang": lang,
            "supported_languages": supported_languages,
            "language_urls": language_urls,
            "t": translations
        }
    )


@router.get("/seo")
async def seo_manager(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """SEO-панель (заглушка)"""
    # Получаем язык и настройки мультиязычности
    lang = get_language_from_request(request)
    supported_languages = get_supported_languages_from_request(request)
    language_urls = get_language_urls_from_request(request)
    
    # Получаем переводы для CMS SEO Manager
    translations = get_cms_seo_translations(lang)
    
    return templates.TemplateResponse(
        "seo.html",
        {
            "request": request,
            "user_email": current_user.get("email", "Пользователь"),
            "lang": lang,
            "supported_languages": supported_languages,
            "language_urls": language_urls,
            "t": translations
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
    translations = get_cms_users_translations(lang)
    
    return templates.TemplateResponse(
        "users.html",
        {
            "request": request,
            "user_email": current_user.get("email", "Пользователь"),
            "lang": lang,
            "supported_languages": supported_languages,
            "language_urls": language_urls,
            "t": translations
        }
    )


# Многоязычные маршруты для users
@router.get("/ru/users")
async def users_ru(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    return await users_manager(request, current_user)


@router.get("/en/users")
async def users_en(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    return await users_manager(request, current_user)


@router.get("/ua/users")
async def users_ua(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    return await users_manager(request, current_user)


# Языковые алиасы для всех CMS страниц
@router.get("/ru/")
async def dashboard_ru(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    return await dashboard(request, current_user)

@router.get("/en/")
async def dashboard_en(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    return await dashboard(request, current_user)

@router.get("/ua/")
async def dashboard_ua(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    return await dashboard(request, current_user)

@router.get("/ru/texts")
async def texts_ru(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    return await texts_editor(request, current_user)

@router.get("/en/texts")
async def texts_en(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    return await texts_editor(request, current_user)

@router.get("/ua/texts")
async def texts_ua(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    return await texts_editor(request, current_user)

@router.get("/ru/images")
async def images_ru(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    return await images_manager(request, current_user)

@router.get("/en/images")
async def images_en(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    return await images_manager(request, current_user)

@router.get("/ua/images")
async def images_ua(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    return await images_manager(request, current_user)

@router.get("/ru/seo")
async def seo_ru(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    return await seo_manager(request, current_user)

@router.get("/en/seo")
async def seo_en(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    return await seo_manager(request, current_user)

@router.get("/ua/seo")
async def seo_ua(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    return await seo_manager(request, current_user)


# API для работы с текстами
@router.get("/api/texts")
async def get_texts(page: str, lang: str, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Получить тексты для указанной страницы и языка"""
    try:
        # Валидация параметров
        valid_pages = ["home", "about", "catalog", "contacts"]
        valid_langs = ["ru", "en", "ua"]
        
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
            FROM texts 
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
        valid_pages = ["home", "about", "catalog", "contacts"]
        valid_langs = ["ru", "en", "ua"]
        
        if not page or page not in valid_pages:
            return {"success": False, "message": f"Недопустимая страница. Доступные: {', '.join(valid_pages)}"}
        
        if not lang or lang not in valid_langs:
            return {"success": False, "message": f"Недопустимый язык. Доступные: {', '.join(valid_langs)}"}
        
        if not isinstance(texts, dict):
            return {"success": False, "message": "Тексты должны быть объектом"}
        
        # Валидация ключей текстов
        valid_keys = ["title", "subtitle", "description", "cta_text", "phone", "address"]
        for key in texts.keys():
            if key not in valid_keys:
                return {"success": False, "message": f"Недопустимый ключ текста: {key}. Доступные: {', '.join(valid_keys)}"}
        
        # Сохраняем каждый текст через UPSERT
        for key, value in texts.items():
            if value:  # Сохраняем только непустые значения
                # Проверяем, существует ли запись
                existing = query_one(
                    "SELECT id FROM texts WHERE page = ? AND key = ? AND lang = ?",
                    (page, key, lang)
                )
                
                if existing:
                    # Обновляем существующую запись
                    execute(
                        "UPDATE texts SET value = ? WHERE page = ? AND key = ? AND lang = ?",
                        (str(value), page, key, lang)
                    )
                else:
                    # Создаем новую запись
                    execute(
                        "INSERT INTO texts (page, key, lang, value) VALUES (?, ?, ?, ?)",
                        (page, key, lang, str(value))
                    )
        
        # Удаляем пустые значения из БД
        for key in valid_keys:
            if key not in texts or not texts[key]:
                delete_query = "DELETE FROM texts WHERE page = ? AND key = ? AND lang = ?"
                execute(delete_query, (page, key, lang))
        
        # Инвалидируем кэш для этой страницы и языка
        text_cache.invalidate(page, lang)
        invalidate_content_caches(page=page, lang=lang)
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
    try:
        images = query_all("""
            SELECT id, name, path, original_path, type, "order"
            FROM images 
            ORDER BY type, "order"
        """)
        
        return {
            "success": True,
            "images": images
        }
    except Exception as e:
        logger.error(f"Ошибка получения списка изображений: {e}")
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
        
        # Проверка типа изображения
        valid_types = ['logo', 'slider', 'background', 'favicon']
        if image_type not in valid_types:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": f"Недопустимый тип изображения. Разрешены: {', '.join(valid_types)}"}
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
        
        # Сохраняем информацию в БД
        execute("""
            INSERT INTO images (name, path, original_path, type, "order")
            VALUES (?, ?, ?, ?, ?)
        """, (unique_filename, optimized_path, original_path, image_type, next_order))
        
        # Получаем ID созданной записи
        image_id = query_one("SELECT last_insert_rowid() as id")["id"]
        
        # Инвалидируем кэш изображений для данного типа
        image_cache.invalidate_type(image_type)
        # Инвалидируем файловый кэш для всех страниц (изображения могут использоваться везде)
        invalidate_content_caches()
        
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
        # Инвалидируем файловый кэш для всех страниц
        invalidate_content_caches()
        
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
        valid_types = ['logo', 'slider', 'background', 'favicon']
        if image_type not in valid_types:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": f"Недопустимый тип изображения. Разрешены: {', '.join(valid_types)}"}
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


# ===== API для работы с SEO =====

@router.get("/api/seo")
async def get_seo(page: str, lang: str, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Получить SEO данные для указанной страницы и языка"""
    try:
        # Валидация параметров
        valid_pages = ["home", "about", "catalog", "contacts"]
        valid_langs = ["ru", "en", "ua"]
        
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
        valid_pages = ["home", "about", "catalog", "contacts"]
        valid_langs = ["ru", "en", "ua"]
        
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
        
        # Инвалидируем кэш для этой страницы и языка
        invalidate_content_caches(page=page, lang=lang)
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
        
        # Хэшируем пароль с учетом ограничений bcrypt
        password_hash = safe_hash_password(password)
        
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
        
        # Хэшируем новый пароль с учетом ограничений bcrypt
        password_hash = safe_hash_password(new_password)
        
        # Обновляем пароль
        execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
        
        return {"success": True, "message": "Пароль успешно сброшен"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка сброса пароля: {e}")
        return {"success": False, "message": "Ошибка сброса пароля"}


# Мультиязычные роуты для CMS
@router.get("/ru/")
async def dashboard_ru(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Dashboard на русском языке"""
    # Устанавливаем русский язык в состояние запроса
    return await dashboard(request, current_user)

@router.get("/en/")
async def dashboard_en(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Dashboard на английском языке"""
    # Устанавливаем английский язык в состояние запроса
    return await dashboard(request, current_user)

@router.get("/ua/")
async def dashboard_ua(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Dashboard на украинском языке"""
    # Устанавливаем украинский язык в состояние запроса
    return await dashboard(request, current_user)

# Мультиязычные роуты для других CMS страниц
@router.get("/ru/texts")
async def texts_ru(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Страница редактирования текстов на русском языке"""
    return await texts_editor(request, current_user)

@router.get("/en/texts")
async def texts_en(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Страница редактирования текстов на английском языке"""
    return await texts_editor(request, current_user)

@router.get("/ua/texts")
async def texts_ua(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Страница редактирования текстов на украинском языке"""
    return await texts_editor(request, current_user)

# Мультиязычные роуты для Images Manager
@router.get("/ru/images")
async def images_ru(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Страница управления изображениями на русском языке"""
    return await images_manager(request, current_user)

@router.get("/en/images")
async def images_en(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Страница управления изображениями на английском языке"""
    return await images_manager(request, current_user)

@router.get("/ua/images")
async def images_ua(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Страница управления изображениями на украинском языке"""
    return await images_manager(request, current_user)

# Мультиязычные роуты для SEO Manager
@router.get("/ru/seo")
async def seo_ru(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Страница SEO-настроек на русском языке"""
    return await seo_manager(request, current_user)

@router.get("/en/seo")
async def seo_en(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Страница SEO-настроек на английском языке"""
    return await seo_manager(request, current_user)

@router.get("/ua/seo")
async def seo_ua(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Страница SEO-настроек на украинском языке"""
    return await seo_manager(request, current_user)