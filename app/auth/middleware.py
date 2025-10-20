from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


class AuthRedirectMiddleware(BaseHTTPMiddleware):
    """Middleware для редиректа неавторизованных пользователей на страницу логина"""
    
    async def dispatch(self, request: Request, call_next):
        # Проверяем, нужна ли авторизация для этого пути
        # Исключаем статические файлы и API endpoints
        if (request.url.path.startswith("/cms") and 
            not request.url.path.startswith("/cms/static") and
            not request.url.path.startswith("/cms/api")):
            # Проверяем наличие токена
            token = request.cookies.get("access_token")
            if not token:
                logger.info(f"No token found for {request.url.path}, redirecting to login")
                return RedirectResponse(url="/login", status_code=302)
            
            # Проверяем валидность токена
            from app.auth.security import decode_token
            payload = decode_token(token)
            if not payload:
                logger.info(f"Invalid token for {request.url.path}, redirecting to login")
                return RedirectResponse(url="/login", status_code=302)
            
            # Проверяем, что пользователь существует в БД
            from app.database.db import query_one
            user_id = payload.get("sub")
            if not user_id:
                logger.info(f"No user ID in token for {request.url.path}, redirecting to login")
                return RedirectResponse(url="/login", status_code=302)
            
            user = query_one("SELECT id FROM users WHERE id = ?", (user_id,))
            if not user:
                logger.info(f"User {user_id} not found in DB for {request.url.path}, redirecting to login")
                return RedirectResponse(url="/login", status_code=302)
        
        try:
            response = await call_next(request)
            return response
        except HTTPException as exc:
            # Если это 401 ошибка и запрос к CMS, делаем редирект на логин
            if exc.status_code == 401 and request.url.path.startswith("/cms"):
                logger.info(f"401 error for {request.url.path}, redirecting to login")
                return RedirectResponse(url="/login", status_code=302)
            # Для других ошибок возвращаем как есть
            raise exc

