import os
import secrets
from typing import Callable

from fastapi import Request, Response
from urllib.parse import parse_qs
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


CSRF_COOKIE_NAME = os.getenv("CSRF_COOKIE_NAME", "csrftoken")
CSRF_HEADER_NAME = os.getenv("CSRF_HEADER_NAME", "x-csrf-token")


def _is_safe_method(method: str) -> bool:
    return method.upper() in {"GET", "HEAD", "OPTIONS", "TRACE"}


class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, cookie_name: str = CSRF_COOKIE_NAME) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.cookie_name = cookie_name

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        token = request.cookies.get(self.cookie_name)
        if not token:
            token = secrets.token_urlsafe(32)
        
        # Пропускаем CSRF проверку для API endpoints
        if request.url.path.startswith("/cms/api/") or request.url.path.startswith("/api/"):
            response = await call_next(request)
            response.set_cookie(self.cookie_name, token, httponly=False, samesite="lax")
            return response
            
        if not _is_safe_method(request.method):
            header = request.headers.get(CSRF_HEADER_NAME)
            if not header or header != token:
                # Попытка валидации через скрытое поле формы csrf_token для обычных form POST
                try:
                    body = await request.body()
                    content_type = request.headers.get("content-type", "")
                    if "application/x-www-form-urlencoded" in content_type:
                        form = parse_qs(body.decode(errors="ignore"))
                        form_token = (form.get("csrf_token") or [""])[0]
                        if form_token != token:
                            return Response(status_code=403)
                        # Восстанавливаем тело для downstream
                        request._body = body  # type: ignore[attr-defined]
                    else:
                        return Response(status_code=403)
                except Exception:
                    return Response(status_code=403)
        response = await call_next(request)
        response.set_cookie(self.cookie_name, token, httponly=False, samesite="lax")
        return response


