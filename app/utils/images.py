"""
Утилиты для работы с изображениями
"""
import os
import uuid
import io
from PIL import Image
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Поддерживаемые форматы
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.ico'}
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/x-icon'}

# Максимальный размер файла (2MB)
MAX_FILE_SIZE = 2 * 1024 * 1024

# Настройки оптимизации
WEBP_QUALITY = 80
MAX_WIDTH = 1920


def validate_image_file(file_content: bytes, filename: str, content_type: str) -> Tuple[bool, str]:
    """
    Валидация загружаемого изображения
    
    Args:
        file_content: содержимое файла
        filename: имя файла
        content_type: MIME тип
    
    Returns:
        (is_valid, error_message)
    """
    # Проверка размера файла
    if len(file_content) > MAX_FILE_SIZE:
        return False, f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE // (1024*1024)}MB"
    
    # Проверка расширения файла
    file_ext = os.path.splitext(filename.lower())[1]
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"Неподдерживаемый формат файла. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Проверка MIME типа
    if content_type not in ALLOWED_MIME_TYPES:
        return False, f"Неподдерживаемый MIME тип. Разрешены: {', '.join(ALLOWED_MIME_TYPES)}"
    
    # Проверка, что файл является валидным изображением
    try:
        with Image.open(io.BytesIO(file_content)) as img:
            img.verify()
    except Exception as e:
        return False, f"Файл не является валидным изображением: {str(e)}"
    
    return True, ""


def optimize_image(file_content: bytes, output_path: str, max_width: int = MAX_WIDTH, quality: int = WEBP_QUALITY) -> bool:
    """
    Оптимизация изображения и сохранение в WebP формате
    
    Args:
        file_content: содержимое оригинального файла
        output_path: путь для сохранения оптимизированного изображения
        max_width: максимальная ширина
        quality: качество WebP (0-100)
    
    Returns:
        True если успешно, False иначе
    """
    try:
        import io
        
        # Создаем директорию если не существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with Image.open(io.BytesIO(file_content)) as img:
            # Конвертируем в RGB если необходимо
            if img.mode in ('RGBA', 'LA', 'P'):
                # Создаем белый фон для прозрачных изображений
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Изменяем размер если изображение слишком широкое
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Сохраняем в WebP формате
            img.save(output_path, 'WEBP', quality=quality, optimize=True)
            
        logger.info(f"Изображение оптимизировано и сохранено: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка оптимизации изображения: {e}")
        return False


def save_original_image(file_content: bytes, original_path: str) -> bool:
    """
    Сохранение оригинального изображения
    
    Args:
        file_content: содержимое файла
        original_path: путь для сохранения оригинала
    
    Returns:
        True если успешно, False иначе
    """
    try:
        # Создаем директорию если не существует
        os.makedirs(os.path.dirname(original_path), exist_ok=True)
        
        # Сохраняем оригинальный файл
        with open(original_path, 'wb') as f:
            f.write(file_content)
            
        logger.info(f"Оригинальное изображение сохранено: {original_path}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка сохранения оригинального изображения: {e}")
        return False


def generate_unique_filename(original_filename: str) -> str:
    """
    Генерация уникального имени файла
    
    Args:
        original_filename: оригинальное имя файла
    
    Returns:
        Уникальное имя файла
    """
    # Получаем расширение
    file_ext = os.path.splitext(original_filename)[1]
    
    # Генерируем уникальное имя
    unique_id = str(uuid.uuid4())
    
    return f"{unique_id}{file_ext}"


def get_image_info(file_content: bytes) -> Optional[dict]:
    """
    Получение информации об изображении
    
    Args:
        file_content: содержимое файла
    
    Returns:
        Словарь с информацией об изображении или None
    """
    try:
        import io
        
        with Image.open(io.BytesIO(file_content)) as img:
            return {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode
            }
    except Exception as e:
        logger.error(f"Ошибка получения информации об изображении: {e}")
        return None
