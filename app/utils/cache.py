"""
Модуль кэширования для CMS
In-memory кэш с TTL для текстов и SEO + файловый кэш для статичных рендеров
"""
import time
import logging
import os
import json
import hashlib
from typing import Dict, Any, Optional, Union
from threading import Lock
from pathlib import Path

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
                    cache_metrics.record_hit()
                    return entry["data"]
                else:
                    # Удаляем устаревшую запись
                    del self.cache[cache_key]
                    logger.debug(f"Cache expired for {cache_key}")
            
            cache_metrics.record_miss()
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
            cache_metrics.record_set()
            logger.debug(f"Cache set for {cache_key}, expires at {expires_at}")
    
    def invalidate(self, page: str, lang: str) -> None:
        """Инвалидировать кэш для конкретной страницы и языка"""
        with self.lock:
            cache_key = self._get_cache_key(page, lang)
            if cache_key in self.cache:
                del self.cache[cache_key]
                cache_metrics.record_invalidation()
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
                    cache_metrics.record_hit()
                    return entry["data"]
                else:
                    # Удаляем устаревшую запись
                    del self.cache[cache_key]
                    logger.debug(f"Image cache expired for {cache_key}")
            
            cache_metrics.record_miss()
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
            cache_metrics.record_set()
            logger.debug(f"Image cache set for {cache_key}, expires at {expires_at}")
    
    def invalidate_type(self, image_type: str) -> None:
        """Инвалидировать кэш для конкретного типа изображений"""
        with self.lock:
            cache_key = self._get_cache_key(image_type)
            if cache_key in self.cache:
                del self.cache[cache_key]
                cache_metrics.record_invalidation()
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


class CacheMetrics:
    """Метрики производительности кэша"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.invalidations = 0
        self.render_times = []  # Времена рендера страниц
        self.lock = Lock()
    
    def record_hit(self):
        """Записать попадание в кэш"""
        with self.lock:
            self.hits += 1
    
    def record_miss(self):
        """Записать промах кэша"""
        with self.lock:
            self.misses += 1
    
    def record_set(self):
        """Записать установку в кэш"""
        with self.lock:
            self.sets += 1
    
    def record_invalidation(self):
        """Записать инвалидацию кэша"""
        with self.lock:
            self.invalidations += 1
    
    def record_render_time(self, render_time: float):
        """Записать время рендера страницы"""
        with self.lock:
            self.render_times.append({
                "timestamp": time.time(),
                "render_time": render_time
            })
            # Оставляем только последние 100 записей
            if len(self.render_times) > 100:
                self.render_times = self.render_times[-100:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику метрик"""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            avg_render_time = 0
            if self.render_times:
                avg_render_time = sum(r["render_time"] for r in self.render_times) / len(self.render_times)
            
            return {
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate_percent": round(hit_rate, 2),
                "sets": self.sets,
                "invalidations": self.invalidations,
                "avg_render_time_ms": round(avg_render_time * 1000, 2),
                "total_requests": total_requests
            }


class FileCache:
    """Файловый кэш для статичных рендеров страниц"""
    
    def __init__(self, cache_dir: str = "cache/renders"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.lock = Lock()
    
    def _get_cache_key(self, path: str, lang: str) -> str:
        """Создать ключ кэша для пути и языка"""
        key_string = f"{path}:{lang}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_file(self, cache_key: str) -> Path:
        """Получить путь к файлу кэша"""
        return self.cache_dir / f"{cache_key}.json"
    
    def get(self, path: str, lang: str) -> Optional[Dict[str, Any]]:
        """Получить кэшированный рендер страницы"""
        with self.lock:
            cache_key = self._get_cache_key(path, lang)
            cache_file = self._get_cache_file(cache_key)
            
            if cache_file.exists():
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Проверяем TTL
                    if time.time() < data.get("expires_at", 0):
                        logger.debug(f"File cache hit for {path}:{lang}")
                        return data
                    else:
                        # Удаляем устаревший файл
                        cache_file.unlink()
                        logger.debug(f"File cache expired for {path}:{lang}")
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Corrupted cache file {cache_file}: {e}")
                    cache_file.unlink()
            
            return None
    
    def set(self, path: str, lang: str, content: str, metadata: Dict[str, Any], ttl: int = 3600) -> None:
        """Сохранить рендер страницы в файловый кэш"""
        with self.lock:
            cache_key = self._get_cache_key(path, lang)
            cache_file = self._get_cache_file(cache_key)
            
            data = {
                "content": content,
                "metadata": metadata,
                "path": path,
                "lang": lang,
                "created_at": time.time(),
                "expires_at": time.time() + ttl
            }
            
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logger.debug(f"File cache set for {path}:{lang}")
            except Exception as e:
                logger.error(f"Failed to write cache file {cache_file}: {e}")
    
    def invalidate(self, path: str, lang: str) -> None:
        """Инвалидировать кэш для конкретной страницы и языка"""
        with self.lock:
            cache_key = self._get_cache_key(path, lang)
            cache_file = self._get_cache_file(cache_key)
            
            if cache_file.exists():
                cache_file.unlink()
                logger.debug(f"File cache invalidated for {path}:{lang}")
    
    def invalidate_path(self, path: str) -> None:
        """Инвалидировать кэш для всех языков конкретной страницы"""
        with self.lock:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if data.get("path") == path:
                        cache_file.unlink()
                        logger.debug(f"File cache invalidated for path {path}")
                except (json.JSONDecodeError, KeyError):
                    # Удаляем поврежденный файл
                    cache_file.unlink()
    
    def invalidate_lang(self, lang: str) -> None:
        """Инвалидировать кэш для конкретного языка"""
        with self.lock:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if data.get("lang") == lang:
                        cache_file.unlink()
                        logger.debug(f"File cache invalidated for lang {lang}")
                except (json.JSONDecodeError, KeyError):
                    # Удаляем поврежденный файл
                    cache_file.unlink()
    
    def clear(self) -> None:
        """Очистить весь файловый кэш"""
        with self.lock:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.debug("File cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику файлового кэша"""
        with self.lock:
            files = list(self.cache_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in files)
            
            current_time = time.time()
            active_files = 0
            expired_files = 0
            
            for cache_file in files:
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if current_time < data.get("expires_at", 0):
                        active_files += 1
                    else:
                        expired_files += 1
                except (json.JSONDecodeError, KeyError):
                    expired_files += 1
            
            return {
                "total_files": len(files),
                "active_files": active_files,
                "expired_files": expired_files,
                "total_size_bytes": total_size,
                "cache_dir": str(self.cache_dir)
            }


# Глобальные экземпляры кэша
text_cache = TextCache(default_ttl=300)  # 5 минут TTL
image_cache = ImageCache(default_ttl=600)  # 10 минут TTL
file_cache = FileCache()  # Файловый кэш для рендеров
cache_metrics = CacheMetrics()  # Метрики производительности


def measure_render_time(func):
    """Декоратор для измерения времени рендера страниц"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        render_time = time.time() - start_time
        cache_metrics.record_render_time(render_time)
        return result
    return wrapper


def get_cache_stats() -> Dict[str, Any]:
    """Получить общую статистику всех кэшей"""
    return {
        "text_cache": text_cache.get_stats(),
        "image_cache": image_cache.get_stats(),
        "file_cache": file_cache.get_stats(),
        "metrics": cache_metrics.get_stats()
    }


def clear_all_caches() -> None:
    """Очистить все кэши"""
    text_cache.clear()
    image_cache.clear()
    file_cache.clear()
    logger.info("All caches cleared")


def invalidate_content_caches(page: str = None, lang: str = None) -> None:
    """Инвалидировать кэши при изменении контента"""
    if page:
        text_cache.invalidate_page(page)
        file_cache.invalidate_path(page)
        logger.info(f"Content caches invalidated for page: {page}")
    
    if lang:
        file_cache.invalidate_lang(lang)
        logger.info(f"Content caches invalidated for language: {lang}")
    
    if not page and not lang:
        # Инвалидируем все кэши
        clear_all_caches()
