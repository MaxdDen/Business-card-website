from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from app.auth.security import get_current_user
from app.database.db import query_one, query_all
from typing import Dict, Any
import logging

router = APIRouter(prefix="/cms", tags=["cms"])
templates = Jinja2Templates(directory="app/templates")

logger = logging.getLogger(__name__)


def get_current_user_dependency(request: Request) -> Dict[str, Any]:
    """Зависимость для получения текущего пользователя"""
    return get_current_user(request)


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


@router.get("/")
async def dashboard(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Главная панель CMS"""
    try:
        stats = get_dashboard_stats()
        
        # Получаем информацию о пользователе
        user_email = current_user.get("email", "Пользователь")
        user_role = current_user.get("role", "editor")
        
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user_email": user_email,
                "user_role": user_role,
                "stats": stats
            }
        )
    except Exception as e:
        logger.error(f"Ошибка рендеринга Dashboard: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки панели управления")


@router.get("/texts")
async def texts_editor(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Редактор текстов (заглушка)"""
    return templates.TemplateResponse(
        "texts.html",
        {
            "request": request,
            "user_email": current_user.get("email", "Пользователь")
        }
    )


@router.get("/images")
async def images_manager(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Управление изображениями (заглушка)"""
    return templates.TemplateResponse(
        "images.html",
        {
            "request": request,
            "user_email": current_user.get("email", "Пользователь")
        }
    )


@router.get("/seo")
async def seo_manager(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """SEO-панель (заглушка)"""
    return templates.TemplateResponse(
        "seo.html",
        {
            "request": request,
            "user_email": current_user.get("email", "Пользователь")
        }
    )


@router.get("/users")
async def users_manager(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency)):
    """Управление пользователями (только для admin)"""
    user_role = current_user.get("role", "editor")
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен. Требуется роль admin")
    
    return templates.TemplateResponse(
        "users.html",
        {
            "request": request,
            "user_email": current_user.get("email", "Пользователь")
        }
    )
