import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt

from passlib.context import CryptContext
from passlib.exc import UnknownHashError
import logging

# Настраиваем логирование для отладки
logger = logging.getLogger(__name__)

# Инициализируем контекст с обработкой ошибок
try:
    _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    logger.info("bcrypt context initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize bcrypt context: {e}")
    # Fallback на pbkdf2_sha256 если bcrypt не работает
    _pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
    logger.info("Using pbkdf2_sha256 as fallback")


def hash_password(plain_password: str) -> str:
    try:
        # Ограничиваем длину пароля до 72 байт (ограничение bcrypt)
        password_bytes = plain_password.encode('utf-8')
        original_length = len(password_bytes)
        if len(password_bytes) > 72:
            # Обрезаем до 72 байт и декодируем обратно
            plain_password = password_bytes[:72].decode('utf-8', errors='ignore')
            logger.info(f"Password truncated from {original_length} to {len(plain_password.encode('utf-8'))} bytes during hashing")
        
        result = _pwd_context.hash(plain_password)
        logger.info(f"Password hashed successfully: {result[:20]}...")
        return result
        
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        # Fallback на простой хеш если основное хеширование не работает
        import hashlib
        salt = os.urandom(32)
        hash_obj = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
        fallback_hash = f"pbkdf2_sha256${salt.hex()}${hash_obj.hex()}"
        logger.info(f"Using fallback hash: {fallback_hash[:20]}...")
        return fallback_hash


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        # Ограничиваем длину пароля до 72 байт (ограничение bcrypt)
        password_bytes = plain_password.encode('utf-8')
        original_length = len(password_bytes)
        if len(password_bytes) > 72:
            # Обрезаем до 72 байт и декодируем обратно
            plain_password = password_bytes[:72].decode('utf-8', errors='ignore')
            logger.info(f"Password truncated from {original_length} to {len(plain_password.encode('utf-8'))} bytes")
        
        logger.info(f"Verifying password against hash: {password_hash[:20]}...")
        result = _pwd_context.verify(plain_password, password_hash)
        logger.info(f"Password verification result: {result}")
        return result
        
    except UnknownHashError:
        # Некорректный/устаревший формат хеша – пробуем fallback
        logger.warning("Unknown hash format, trying fallback verification")
        if password_hash.startswith("pbkdf2_sha256$"):
            try:
                parts = password_hash.split("$")
                logger.info(f"Hash parts: {len(parts)}")
                if len(parts) == 3:
                    salt = bytes.fromhex(parts[1])
                    stored_hash = parts[2]
                    logger.info(f"Salt length: {len(salt)}, stored hash length: {len(stored_hash)}")
                    import hashlib
                    hash_obj = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
                    computed_hash = hash_obj.hex()
                    result = computed_hash == stored_hash
                    logger.info(f"Computed hash: {computed_hash[:20]}...")
                    logger.info(f"Stored hash: {stored_hash[:20]}...")
                    logger.info(f"Fallback verification result: {result}")
                    return result
            except Exception as fallback_error:
                logger.error(f"Fallback verification failed: {fallback_error}")
        return False
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        # Fallback для кастомного хеша
        if password_hash.startswith("pbkdf2_sha256$"):
            try:
                parts = password_hash.split("$")
                if len(parts) == 3:
                    salt = bytes.fromhex(parts[1])
                    stored_hash = parts[2]
                    import hashlib
                    # Используем тот же пароль, что и при хешировании (уже обрезанный)
                    hash_obj = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
                    result = hash_obj.hex() == stored_hash
                    logger.info(f"Fallback verification result: {result}")
                    return result
            except Exception as fallback_error:
                logger.error(f"Fallback verification failed: {fallback_error}")
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


