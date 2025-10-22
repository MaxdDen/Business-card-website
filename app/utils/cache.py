"""
Модуль кэширования для CMS
In-memory кэш с TTL для текстов и SEO
"""
import time
import logging
from typing import Dict, Any, Optional
from threading import Lock

logger = logging.getLogger(__name__)

class TextCache:
    """In-memory кэш для текстов с TTL"""
    
    def __init__(self, default_ttl: int = 300):  # 5 минут по умолчанию
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.lock = Lock()
    
    def _get_cache_key(self, page: str, lang: str) -> str:
        """Создать ключ кэша для страницы и языка"""
        return f"texts:{page}:{lang}"
    
    def get(self, page: str, lang: str) -> Optional[Dict[str, str]]:
        """Получить тексты из кэша"""
        with self.lock:
            cache_key = self._get_cache_key(page, lang)
            if cache_key in self.cache:
                entry = self.cache[cache_key]
                # Проверяем TTL
                if time.time() < entry["expires_at"]:
                    logger.debug(f"Cache hit for {cache_key}")
                    return entry["data"]
                else:
                    # Удаляем устаревшую запись
                    del self.cache[cache_key]
                    logger.debug(f"Cache expired for {cache_key}")
            return None
    
    def set(self, page: str, lang: str, texts: Dict[str, str], ttl: Optional[int] = None) -> None:
        """Сохранить тексты в кэш"""
        with self.lock:
            cache_key = self._get_cache_key(page, lang)
            expires_at = time.time() + (ttl or self.default_ttl)
            
            self.cache[cache_key] = {
                "data": texts.copy(),
                "expires_at": expires_at,
                "created_at": time.time()
            }
            logger.debug(f"Cache set for {cache_key}, expires at {expires_at}")
    
    def invalidate(self, page: str, lang: str) -> None:
        """Инвалидировать кэш для конкретной страницы и языка"""
        with self.lock:
            cache_key = self._get_cache_key(page, lang)
            if cache_key in self.cache:
                del self.cache[cache_key]
                logger.debug(f"Cache invalidated for {cache_key}")
    
    def invalidate_page(self, page: str) -> None:
        """Инвалидировать кэш для всей страницы (все языки)"""
        with self.lock:
            keys_to_remove = []
            for cache_key in self.cache.keys():
                if cache_key.startswith(f"texts:{page}:"):
                    keys_to_remove.append(cache_key)
            
            for key in keys_to_remove:
                del self.cache[key]
                logger.debug(f"Cache invalidated for page {page}")
    
    def clear(self) -> None:
        """Очистить весь кэш"""
        with self.lock:
            self.cache.clear()
            logger.debug("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику кэша"""
        with self.lock:
            current_time = time.time()
            active_entries = 0
            expired_entries = 0
            
            for entry in self.cache.values():
                if time.time() < entry["expires_at"]:
                    active_entries += 1
                else:
                    expired_entries += 1
            
            return {
                "total_entries": len(self.cache),
                "active_entries": active_entries,
                "expired_entries": expired_entries,
                "cache_size": len(self.cache)
            }


class ImageCache:
    """In-memory кэш для изображений с TTL"""
    
    def __init__(self, default_ttl: int = 600):  # 10 минут по умолчанию
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.lock = Lock()
    
    def _get_cache_key(self, image_type: str) -> str:
        """Создать ключ кэша для типа изображений"""
        return f"images:{image_type}"
    
    def get(self, image_type: str) -> Optional[list]:
        """Получить изображения из кэша"""
        with self.lock:
            cache_key = self._get_cache_key(image_type)
            if cache_key in self.cache:
                entry = self.cache[cache_key]
                # Проверяем TTL
                if time.time() < entry["expires_at"]:
                    logger.debug(f"Image cache hit for {cache_key}")
                    return entry["data"]
                else:
                    # Удаляем устаревшую запись
                    del self.cache[cache_key]
                    logger.debug(f"Image cache expired for {cache_key}")
            return None
    
    def set(self, image_type: str, images: list, ttl: Optional[int] = None) -> None:
        """Сохранить изображения в кэш"""
        with self.lock:
            cache_key = self._get_cache_key(image_type)
            expires_at = time.time() + (ttl or self.default_ttl)
            
            self.cache[cache_key] = {
                "data": images.copy(),
                "expires_at": expires_at,
                "created_at": time.time()
            }
            logger.debug(f"Image cache set for {cache_key}, expires at {expires_at}")
    
    def invalidate_type(self, image_type: str) -> None:
        """Инвалидировать кэш для конкретного типа изображений"""
        with self.lock:
            cache_key = self._get_cache_key(image_type)
            if cache_key in self.cache:
                del self.cache[cache_key]
                logger.debug(f"Image cache invalidated for {cache_key}")
    
    def invalidate_all(self) -> None:
        """Инвалидировать весь кэш изображений"""
        with self.lock:
            keys_to_remove = []
            for cache_key in self.cache.keys():
                if cache_key.startswith("images:"):
                    keys_to_remove.append(cache_key)
            
            for key in keys_to_remove:
                del self.cache[key]
                logger.debug(f"Image cache invalidated for {key}")
    
    def clear(self) -> None:
        """Очистить весь кэш изображений"""
        with self.lock:
            self.cache.clear()
            logger.debug("Image cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику кэша изображений"""
        with self.lock:
            current_time = time.time()
            active_entries = 0
            expired_entries = 0
            
            for entry in self.cache.values():
                if time.time() < entry["expires_at"]:
                    active_entries += 1
                else:
                    expired_entries += 1
            
            return {
                "total_entries": len(self.cache),
                "active_entries": active_entries,
                "expired_entries": expired_entries,
                "cache_size": len(self.cache)
            }


# Глобальные экземпляры кэша
text_cache = TextCache(default_ttl=300)  # 5 минут TTL
image_cache = ImageCache(default_ttl=600)  # 10 минут TTL
