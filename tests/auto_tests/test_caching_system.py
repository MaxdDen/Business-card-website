"""
Автотест системы кэширования
Проверяет работу in-memory кэша, файлового кэша и метрик производительности
"""

import asyncio
import time
import json
import os
import tempfile
from pathlib import Path
import sys
import logging

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.utils.cache import (
    TextCache, ImageCache, FileCache, CacheMetrics,
    text_cache, image_cache, file_cache, cache_metrics,
    measure_render_time, get_cache_stats, clear_all_caches,
    invalidate_content_caches
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestCachingSystem:
    """Тест системы кэширования"""
    
    def __init__(self):
        self.test_results = []
        self.temp_dir = None
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Логировать результат теста"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
    
    def test_text_cache_basic_operations(self):
        """Тест базовых операций TextCache"""
        try:
            # Создаем новый экземпляр кэша для тестов
            test_cache = TextCache(default_ttl=1)  # 1 секунда TTL для быстрого тестирования
            
            # Тест 1: Установка и получение данных
            test_data = {"title": "Test Title", "description": "Test Description"}
            test_cache.set("home", "ru", test_data)
            
            retrieved_data = test_cache.get("home", "ru")
            success = retrieved_data == test_data
            self.log_test("TextCache: Set/Get", success, 
                         f"Expected: {test_data}, Got: {retrieved_data}")
            
            # Тест 2: Промах кэша для несуществующих данных
            miss_data = test_cache.get("about", "en")
            success = miss_data is None
            self.log_test("TextCache: Cache Miss", success, 
                         f"Expected: None, Got: {miss_data}")
            
            # Тест 3: Инвалидация кэша
            test_cache.invalidate("home", "ru")
            invalidated_data = test_cache.get("home", "ru")
            success = invalidated_data is None
            self.log_test("TextCache: Invalidation", success, 
                         f"Expected: None, Got: {invalidated_data}")
            
            # Тест 4: TTL истечение
            test_cache.set("test", "ru", {"key": "value"})
            time.sleep(1.1)  # Ждем истечения TTL
            expired_data = test_cache.get("test", "ru")
            success = expired_data is None
            self.log_test("TextCache: TTL Expiration", success, 
                         f"Expected: None, Got: {expired_data}")
            
            return True
            
        except Exception as e:
            self.log_test("TextCache: Basic Operations", False, f"Exception: {e}")
            return False
    
    def test_image_cache_operations(self):
        """Тест операций ImageCache"""
        try:
            # Создаем новый экземпляр кэша для тестов
            test_cache = ImageCache(default_ttl=1)
            
            # Тест 1: Установка и получение изображений
            test_images = [
                {"path": "/uploads/img1.webp", "original_path": "/uploads/originals/img1.jpg"},
                {"path": "/uploads/img2.webp", "original_path": "/uploads/originals/img2.jpg"}
            ]
            test_cache.set("slider", test_images)
            
            retrieved_images = test_cache.get("slider")
            success = retrieved_images == test_images
            self.log_test("ImageCache: Set/Get", success, 
                         f"Expected: {len(test_images)} images, Got: {len(retrieved_images) if retrieved_images else 0}")
            
            # Тест 2: Инвалидация по типу
            test_cache.invalidate_type("slider")
            invalidated_images = test_cache.get("slider")
            success = invalidated_images is None
            self.log_test("ImageCache: Type Invalidation", success, 
                         f"Expected: None, Got: {invalidated_images}")
            
            return True
            
        except Exception as e:
            self.log_test("ImageCache: Operations", False, f"Exception: {e}")
            return False
    
    def test_file_cache_operations(self):
        """Тест операций FileCache"""
        try:
            # Создаем временную директорию для тестов
            self.temp_dir = tempfile.mkdtemp()
            test_cache = FileCache(cache_dir=self.temp_dir)
            
            # Тест 1: Установка и получение файлового кэша
            test_content = "<html><body>Test Content</body></html>"
            test_metadata = {"template": "test.html", "path": "/test", "lang": "ru"}
            test_cache.set("/test", "ru", test_content, test_metadata, ttl=1)
            
            cached_data = test_cache.get("/test", "ru")
            success = cached_data is not None and cached_data["content"] == test_content
            self.log_test("FileCache: Set/Get", success, 
                         f"Expected content, Got: {cached_data['content'][:50] if cached_data else None}")
            
            # Тест 2: TTL истечение
            time.sleep(1.1)
            expired_data = test_cache.get("/test", "ru")
            success = expired_data is None
            self.log_test("FileCache: TTL Expiration", success, 
                         f"Expected: None, Got: {expired_data}")
            
            # Тест 3: Инвалидация по пути
            test_cache.set("/test", "ru", test_content, test_metadata, ttl=10)
            test_cache.invalidate_path("/test")
            invalidated_data = test_cache.get("/test", "ru")
            success = invalidated_data is None
            self.log_test("FileCache: Path Invalidation", success, 
                         f"Expected: None, Got: {invalidated_data}")
            
            return True
            
        except Exception as e:
            self.log_test("FileCache: Operations", False, f"Exception: {e}")
            return False
    
    def test_cache_metrics(self):
        """Тест метрик кэша"""
        try:
            # Создаем новый экземпляр метрик для тестов
            test_metrics = CacheMetrics()
            
            # Тест 1: Запись метрик
            test_metrics.record_hit()
            test_metrics.record_hit()
            test_metrics.record_miss()
            test_metrics.record_set()
            test_metrics.record_invalidation()
            test_metrics.record_render_time(0.1)
            test_metrics.record_render_time(0.2)
            
            stats = test_metrics.get_stats()
            success = (stats["hits"] == 2 and stats["misses"] == 1 and 
                      stats["sets"] == 1 and stats["invalidations"] == 1)
            self.log_test("CacheMetrics: Recording", success, 
                         f"Stats: {stats}")
            
            # Тест 2: Hit rate calculation
            expected_hit_rate = 66.67  # 2 hits out of 3 total requests
            success = abs(stats["hit_rate_percent"] - expected_hit_rate) < 0.01
            self.log_test("CacheMetrics: Hit Rate", success, 
                         f"Expected: ~{expected_hit_rate}%, Got: {stats['hit_rate_percent']}%")
            
            # Тест 3: Average render time
            expected_avg_time = 150.0  # (100 + 200) / 2 = 150ms
            success = abs(stats["avg_render_time_ms"] - expected_avg_time) < 1.0
            self.log_test("CacheMetrics: Average Render Time", success, 
                         f"Expected: ~{expected_avg_time}ms, Got: {stats['avg_render_time_ms']}ms")
            
            return True
            
        except Exception as e:
            self.log_test("CacheMetrics: Operations", False, f"Exception: {e}")
            return False
    
    def test_measure_render_time_decorator(self):
        """Тест декоратора измерения времени рендера"""
        try:
            # Создаем новый экземпляр метрик для тестов
            test_metrics = CacheMetrics()
            
            # Создаем тестовую функцию с декоратором
            @measure_render_time
            def test_render_function():
                time.sleep(0.1)  # Имитируем рендер
                return "rendered content"
            
            # Вызываем функцию несколько раз
            for _ in range(3):
                result = test_render_function()
            
            # Проверяем, что метрики записались
            stats = cache_metrics.get_stats()
            success = stats["total_requests"] >= 3  # Должно быть минимум 3 записи
            self.log_test("Render Time Decorator", success, 
                         f"Total requests: {stats['total_requests']}")
            
            return True
            
        except Exception as e:
            self.log_test("Render Time Decorator", False, f"Exception: {e}")
            return False
    
    def test_cache_integration(self):
        """Тест интеграции всех компонентов кэширования"""
        try:
            # Очищаем все кэши перед тестом
            clear_all_caches()
            
            # Тест 1: Работа с глобальными экземплярами
            test_texts = {"title": "Integration Test", "description": "Test Description"}
            text_cache.set("home", "ru", test_texts)
            
            retrieved_texts = text_cache.get("home", "ru")
            success = retrieved_texts == test_texts
            self.log_test("Integration: Text Cache", success, 
                         f"Expected: {test_texts}, Got: {retrieved_texts}")
            
            # Тест 2: Работа с изображениями
            test_images = [{"path": "/test/img.webp", "original_path": "/test/original.jpg"}]
            image_cache.set("slider", test_images)
            
            retrieved_images = image_cache.get("slider")
            success = retrieved_images == test_images
            self.log_test("Integration: Image Cache", success, 
                         f"Expected: {len(test_images)} images, Got: {len(retrieved_images) if retrieved_images else 0}")
            
            # Тест 3: Получение общей статистики
            stats = get_cache_stats()
            success = ("text_cache" in stats and "image_cache" in stats and 
                      "file_cache" in stats and "metrics" in stats)
            self.log_test("Integration: Cache Stats", success, 
                         f"Stats keys: {list(stats.keys())}")
            
            # Тест 4: Инвалидация контента
            invalidate_content_caches(page="home", lang="ru")
            invalidated_texts = text_cache.get("home", "ru")
            success = invalidated_texts is None
            self.log_test("Integration: Content Invalidation", success, 
                         f"Expected: None, Got: {invalidated_texts}")
            
            return True
            
        except Exception as e:
            self.log_test("Cache Integration", False, f"Exception: {e}")
            return False
    
    def test_performance_metrics(self):
        """Тест производительности кэширования"""
        try:
            # Очищаем кэши
            clear_all_caches()
            
            # Тест 1: Измерение времени без кэша
            start_time = time.time()
            for i in range(100):
                text_cache.set(f"page{i}", "ru", {"title": f"Title {i}"})
            no_cache_time = time.time() - start_time
            
            # Тест 2: Измерение времени с кэшем
            start_time = time.time()
            for i in range(100):
                text_cache.get(f"page{i}", "ru")
            cache_time = time.time() - start_time
            
            # Проверяем, что кэш быстрее
            speedup = no_cache_time / cache_time if cache_time > 0 else float('inf')
            success = speedup > 1.0
            self.log_test("Performance: Cache Speedup", success, 
                         f"Speedup: {speedup:.2f}x (No cache: {no_cache_time:.4f}s, With cache: {cache_time:.4f}s)")
            
            # Тест 3: Проверка метрик производительности
            stats = cache_metrics.get_stats()
            success = stats["hits"] >= 100  # Должно быть 100 попаданий
            self.log_test("Performance: Cache Hits", success, 
                         f"Hits: {stats['hits']}, Hit rate: {stats['hit_rate_percent']}%")
            
            return True
            
        except Exception as e:
            self.log_test("Performance Metrics", False, f"Exception: {e}")
            return False
    
    def cleanup(self):
        """Очистка после тестов"""
        try:
            # Очищаем все кэши
            clear_all_caches()
            
            # Удаляем временную директорию
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        logger.info("🚀 Запуск автотестов системы кэширования")
        logger.info("=" * 60)
        
        try:
            # Запускаем все тесты
            self.test_text_cache_basic_operations()
            self.test_image_cache_operations()
            self.test_file_cache_operations()
            self.test_cache_metrics()
            self.test_measure_render_time_decorator()
            self.test_cache_integration()
            self.test_performance_metrics()
            
            # Подсчитываем результаты
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result["success"])
            failed_tests = total_tests - passed_tests
            
            logger.info("=" * 60)
            logger.info(f"📊 Результаты тестирования:")
            logger.info(f"   Всего тестов: {total_tests}")
            logger.info(f"   ✅ Пройдено: {passed_tests}")
            logger.info(f"   ❌ Провалено: {failed_tests}")
            logger.info(f"   📈 Успешность: {(passed_tests/total_tests)*100:.1f}%")
            
            if failed_tests > 0:
                logger.info("\n❌ Проваленные тесты:")
                for result in self.test_results:
                    if not result["success"]:
                        logger.info(f"   - {result['test']}: {result['message']}")
            
            # Показываем финальную статистику кэша
            logger.info("\n📈 Финальная статистика кэша:")
            final_stats = get_cache_stats()
            for cache_type, stats in final_stats.items():
                if isinstance(stats, dict):
                    logger.info(f"   {cache_type}: {stats}")
            
            return failed_tests == 0
            
        except Exception as e:
            logger.error(f"Ошибка при запуске тестов: {e}")
            return False
        
        finally:
            self.cleanup()

def main():
    """Главная функция для запуска тестов"""
    print("🧪 Автотест системы кэширования CMS")
    print("Проверяет работу in-memory кэша, файлового кэша и метрик производительности")
    print()
    
    # Создаем и запускаем тесты
    tester = TestCachingSystem()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Все тесты системы кэширования пройдены успешно!")
        print("Система кэширования работает корректно.")
    else:
        print("\n⚠️  Некоторые тесты системы кэширования провалились.")
        print("Проверьте логи выше для деталей.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
