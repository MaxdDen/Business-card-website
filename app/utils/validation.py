"""
Утилиты для валидации и безопасности входных данных
"""
import re
import html
from typing import Optional, Tuple
import unicodedata


# Константы валидации
MAX_TEXT_LENGTH = 10000  # Максимальная длина текстового поля
MAX_TITLE_LENGTH = 200
MAX_EMAIL_LENGTH = 255
MAX_PASSWORD_LENGTH = 72  # Ограничение bcrypt


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Очистка строки от потенциально опасных символов
    
    Args:
        value: строка для очистки
        max_length: максимальная длина (опционально)
    
    Returns:
        Очищенная строка
    """
    if not value:
        return ""
    
    # Удаляем управляющие символы
    value = "".join(ch for ch in value if unicodedata.category(ch)[0] != "C" or ch in "\n\r\t")
    
    # Обрезаем до максимальной длины
    if max_length and len(value) > max_length:
        value = value[:max_length]
    
    return value.strip()


def sanitize_html(value: str) -> str:
    """
    Экранирование HTML символов для предотвращения XSS
    
    Args:
        value: строка для экранирования
    
    Returns:
        Экранированная строка
    """
    return html.escape(value, quote=True)


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Валидация email адреса
    
    Args:
        email: email для проверки
    
    Returns:
        (is_valid, error_message)
    """
    if not email:
        return False, "Email не может быть пустым"
    
    if len(email) > MAX_EMAIL_LENGTH:
        return False, f"Email слишком длинный (максимум {MAX_EMAIL_LENGTH} символов)"
    
    # Базовая проверка формата email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Неверный формат email"
    
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Валидация пароля
    
    Args:
        password: пароль для проверки
    
    Returns:
        (is_valid, error_message)
    """
    if not password:
        return False, "Пароль не может быть пустым"
    
    if len(password) < 8:
        return False, "Минимальная длина пароля — 8 символов"
    
    if len(password.encode('utf-8')) > MAX_PASSWORD_LENGTH:
        return False, f"Пароль слишком длинный (максимум {MAX_PASSWORD_LENGTH} байт)"
    
    # Проверка на наличие хотя бы одной буквы и одной цифры
    if not re.search(r'[a-zA-Z]', password):
        return False, "Пароль должен содержать хотя бы одну букву"
    
    if not re.search(r'[0-9]', password):
        return False, "Пароль должен содержать хотя бы одну цифру"
    
    return True, ""


def validate_text_content(content: str, field_name: str = "Поле", max_length: Optional[int] = None) -> Tuple[bool, str]:
    """
    Валидация текстового контента
    
    Args:
        content: текст для проверки
        field_name: название поля для сообщения об ошибке
        max_length: максимальная длина (опционально)
    
    Returns:
        (is_valid, error_message)
    """
    if max_length is None:
        max_length = MAX_TEXT_LENGTH
    
    if len(content) > max_length:
        return False, f"{field_name} превышает максимальную длину ({max_length} символов)"
    
    return True, ""


def sanitize_filename(filename: str) -> str:
    """
    Очистка имени файла от опасных символов
    
    Args:
        filename: оригинальное имя файла
    
    Returns:
        Безопасное имя файла
    """
    # Удаляем путь если есть
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Разрешаем только буквы, цифры, точки, дефисы и подчеркивания
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Удаляем множественные точки (защита от path traversal)
    filename = re.sub(r'\.{2,}', '.', filename)
    
    # Ограничиваем длину имени файла
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename


def validate_page_key(page: str, key: str) -> Tuple[bool, str]:
    """
    Валидация ключа страницы для текстов
    
    Args:
        page: название страницы
        key: ключ текста
    
    Returns:
        (is_valid, error_message)
    """
    valid_pages = ["home", "about", "catalog", "contacts"]
    valid_keys = ["title", "subtitle", "description", "cta_text", "phone", "address", "email"]
    
    if page not in valid_pages:
        return False, f"Недопустимая страница. Доступные: {', '.join(valid_pages)}"
    
    if key not in valid_keys:
        return False, f"Недопустимый ключ. Доступные: {', '.join(valid_keys)}"
    
    return True, ""


def validate_language(lang: str) -> Tuple[bool, str]:
    """
    Валидация языка
    
    Args:
        lang: код языка
    
    Returns:
        (is_valid, error_message)
    """
    valid_langs = ["en", "ua", "ru"]
    
    if lang not in valid_langs:
        return False, f"Недопустимый язык. Доступные: {', '.join(valid_langs)}"
    
    return True, ""


def detect_sql_injection(value: str) -> bool:
    """
    Простая проверка на попытку SQL инъекции
    
    Args:
        value: строка для проверки
    
    Returns:
        True если обнаружена подозрительная активность
    """
    # Паттерны потенциально опасных SQL операций
    dangerous_patterns = [
        r'\bUNION\b.*\bSELECT\b',
        r'\bDROP\b.*\bTABLE\b',
        r'\bDELETE\b.*\bFROM\b',
        r'\bINSERT\b.*\bINTO\b',
        r'\bUPDATE\b.*\bSET\b',
        r'--',
        r'/\*.*\*/',
        r'\bEXEC\b',
        r'\bEXECUTE\b',
        r'\bSCRIPT\b',
    ]
    
    value_upper = value.upper()
    for pattern in dangerous_patterns:
        if re.search(pattern, value_upper, re.IGNORECASE):
            return True
    
    return False


def detect_xss(value: str) -> bool:
    """
    Простая проверка на попытку XSS атаки
    
    Args:
        value: строка для проверки
    
    Returns:
        True если обнаружена подозрительная активность
    """
    # Паттерны потенциально опасных XSS векторов
    dangerous_patterns = [
        r'<script[^>]*>',
        r'javascript:',
        r'onerror\s*=',
        r'onload\s*=',
        r'onclick\s*=',
        r'<iframe[^>]*>',
        r'<embed[^>]*>',
        r'<object[^>]*>',
    ]
    
    value_lower = value.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, value_lower, re.IGNORECASE):
            return True
    
    return False

