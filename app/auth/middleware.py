from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import jwt
from datetime import datetime, timezone
from app.site.middleware import get_language_from_request

logger = logging.getLogger(__name__)


class AuthRedirectMiddleware(BaseHTTPMiddleware):
    """Middleware для редиректа неавторизованных пользователей на страницу логина с сохранением URL"""
    
    async def dispatch(self, request: Request, call_next):
        # Проверяем, нужна ли авторизация для этого пути
        # Исключаем статические файлы и API endpoints
        if (request.url.path.startswith("/cms") and 
            not request.url.path.startswith("/cms/static") and
            not request.url.path.startswith("/cms/api")):
            
            # Получаем язык для корректного редиректа
            lang = get_language_from_request(request)
            
            # Проверяем наличие токена
            token = request.cookies.get("access_token")
            if not token:
                logger.info(f"No token found for {request.url.path}, redirecting to login")
                redirect_url = f"/{lang}/login?next={request.url.path}"
                return RedirectResponse(url=redirect_url, status_code=302)
            
            # Проверяем валидность токена и его истечение
            try:
                from app.auth.security import decode_token
                payload = decode_token(token)
                if not payload:
                    logger.info(f"Invalid token for {request.url.path}, redirecting to login")
                    redirect_url = f"/{lang}/login?next={request.url.path}"
                    return RedirectResponse(url=redirect_url, status_code=302)
                
                # Проверяем истечение токена
                exp_timestamp = payload.get("exp")
                if exp_timestamp:
                    current_time = datetime.now(timezone.utc).timestamp()
                    if current_time >= exp_timestamp:
                        logger.info(f"Token expired for {request.url.path}, redirecting to login")
                        redirect_url = f"/{lang}/login?next={request.url.path}"
                        return RedirectResponse(url=redirect_url, status_code=302)
                
            except jwt.ExpiredSignatureError:
                logger.info(f"Token expired for {request.url.path}, redirecting to login")
                redirect_url = f"/{lang}/login?next={request.url.path}"
                return RedirectResponse(url=redirect_url, status_code=302)
            except jwt.InvalidTokenError:
                logger.info(f"Invalid token for {request.url.path}, redirecting to login")
                redirect_url = f"/{lang}/login?next={request.url.path}"
                return RedirectResponse(url=redirect_url, status_code=302)
            
            # Проверяем, что пользователь существует в БД
            from app.database.db import query_one
            user_id = payload.get("sub")
            if not user_id:
                logger.info(f"No user ID in token for {request.url.path}, redirecting to login")
                redirect_url = f"/{lang}/login?next={request.url.path}"
                return RedirectResponse(url=redirect_url, status_code=302)
            
            user = query_one("SELECT id FROM users WHERE id = ?", (user_id,))
            if not user:
                logger.info(f"User {user_id} not found in DB for {request.url.path}, redirecting to login")
                redirect_url = f"/{lang}/login?next={request.url.path}"
                return RedirectResponse(url=redirect_url, status_code=302)
        
        try:
            response = await call_next(request)
            return response
        except HTTPException as exc:
            # Если это 401 ошибка и запрос к CMS, делаем редирект на логин
            if exc.status_code == 401 and request.url.path.startswith("/cms"):
                logger.info(f"401 error for {request.url.path}, redirecting to login")
                lang = get_language_from_request(request)
                redirect_url = f"/{lang}/login?next={request.url.path}"
                return RedirectResponse(url=redirect_url, status_code=302)
            # Для других ошибок возвращаем как есть
            raise exc

