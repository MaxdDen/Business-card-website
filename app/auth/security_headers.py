"""
Security Headers Middleware для защиты приложения
"""
import os
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi import Request, Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware для добавления заголовков безопасности
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.is_production = os.getenv("ENVIRONMENT", "development") == "production"
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        
        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # unsafe-inline нужен для inline scripts
            "style-src 'self' 'unsafe-inline'",  # unsafe-inline нужен для Tailwind
            "img-src 'self' data: blob:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # X-Frame-Options - защита от clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options - предотвращение MIME-sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection - дополнительная защита от XSS (legacy браузеры)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy - контроль передачи referrer
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy - контроль браузерных фич
        permissions = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)
        
        # Strict-Transport-Security - только для production с HTTPS
        if self.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


def set_secure_cookie(
    response: Response,
    key: str,
    value: str,
    max_age: int = None,
    httponly: bool = True,
    samesite: str = "lax"
) -> None:
    """
    Установка безопасного cookie
    
    Args:
        response: объект ответа
        key: ключ cookie
        value: значение cookie
        max_age: время жизни в секундах
        httponly: флаг HttpOnly
        samesite: политика SameSite (lax, strict, none)
    """
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    
    response.set_cookie(
        key=key,
        value=value,
        max_age=max_age,
        httponly=httponly,
        samesite=samesite,
        secure=is_production,  # Secure только в production
    )


def delete_secure_cookie(response: Response, key: str) -> None:
    """
    Удаление безопасного cookie
    
    Args:
        response: объект ответа
        key: ключ cookie
    """
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    
    response.delete_cookie(
        key=key,
        httponly=True,
        samesite="lax",
        secure=is_production,
    )

