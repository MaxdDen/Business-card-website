import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
import bcrypt
import logging

# Настраиваем логирование для отладки
logger = logging.getLogger(__name__)

# Используем только bcrypt для хеширования паролей по best practices
logger.info("Using bcrypt for password hashing")


def hash_password(plain_password: str) -> str:
    """Хэширование пароля с использованием bcrypt по best practices"""
    try:
        # bcrypt имеет ограничение в 72 байта для пароля
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
            logger.info(f"Password truncated to 72 bytes for bcrypt compatibility")
        
        # Генерируем соль и хэшируем пароль с помощью bcrypt
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes, salt)
        
        result = password_hash.decode('utf-8')
        logger.info(f"Password hashed successfully with bcrypt: {result[:20]}...")
        return result
        
    except Exception as e:
        logger.error(f"Error hashing password with bcrypt: {e}")
        raise ValueError(f"Failed to hash password: {e}")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Верификация пароля с использованием bcrypt по best practices"""
    try:
        # bcrypt имеет ограничение в 72 байта для пароля
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
            logger.info(f"Password truncated to 72 bytes for bcrypt verification")
        
        # Проверяем пароль с помощью bcrypt
        stored_hash_bytes = password_hash.encode('utf-8')
        result = bcrypt.checkpw(password_bytes, stored_hash_bytes)
        
        logger.info(f"Password verification result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error verifying password with bcrypt: {e}")
        return False


def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise ValueError("JWT_SECRET environment variable is required")
    return secret


def create_access_token(subject: str, role: str, expires_minutes: Optional[int] = None) -> str:
    if expires_minutes is None:
        expires_minutes = int(os.getenv("JWT_EXPIRES_MINUTES", "15"))
    
    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
        "type": "access",
    }
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, _jwt_secret(), algorithms=["HS256"])  # type: ignore[no-any-return]
    except jwt.PyJWTError:
        return None


def get_current_user(request) -> Dict[str, Any]:
    """Получить текущего пользователя из JWT токена"""
    from fastapi import HTTPException
    from fastapi.responses import RedirectResponse
    
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    
    # Получаем дополнительную информацию о пользователе из БД
    from app.database.db import query_one
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    
    user = query_one("SELECT id, email, role FROM users WHERE id = ?", (user_id,))
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    
    return {
        "id": user["id"],
        "email": user["email"],
        "role": user["role"]
    }


def require_admin(request) -> Dict[str, Any]:
    """Получить текущего пользователя и проверить, что он администратор"""
    user = get_current_user(request)
    if user["role"] != "admin":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Требуются права администратора")
    return user


