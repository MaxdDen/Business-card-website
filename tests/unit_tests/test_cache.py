#!/usr/bin/env python3
"""
Юнит-тесты для модуля кэширования
Проверяет функциональность TextCache и SEOCache
"""

import sys
import os
import time
import threading
import unittest
from unittest.mock import patch

# Добавляем путь к модулям приложения
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.utils.cache import TextCache, SEOCache

class TestTextCache(unittest.TestCase):
    """Тесты для TextCache"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.cache = TextCache(default_ttl=1)  # Короткий TTL для тестов
    
    def test_cache_basic_operations(self):
        """Тест базовых операций кэша"""
        # Пустой кэш
        result = self.cache.get("home", "ru")
        self.assertIsNone(result)
        
        # Сохранение данных
        test_data = {"title": "Главная", "description": "Описание"}
        self.cache.set("home", "ru", test_data)
        
        # Получение данных
        result = self.cache.get("home", "ru")
        self.assertEqual(result, test_data)
    
    def test_cache_ttl_expiration(self):
        """Тест истечения TTL"""
        # Сохранение с коротким TTL
        test_data = {"title": "Test"}
        self.cache.set("home", "ru", test_data, ttl=0.1)
        
        # Данные должны быть доступны сразу
        result = self.cache.get("home", "ru")
        self.assertEqual(result, test_data)
        
        # Ждем истечения TTL
        time.sleep(0.2)
        
        # Данные должны исчезнуть
        result = self.cache.get("home", "ru")
        self.assertIsNone(result)
    
    def test_cache_different_keys(self):
        """Тест разных ключей кэша"""
        # Разные страницы
        self.cache.set("home", "ru", {"title": "Главная"})
        self.cache.set("about", "ru", {"title": "О нас"})
        
        home_data = self.cache.get("home", "ru")
        about_data = self.cache.get("about", "ru")
        
        self.assertEqual(home_data["title"], "Главная")
        self.assertEqual(about_data["title"], "О нас")
        
        # Разные языки
        self.cache.set("home", "en", {"title": "Home"})
        en_data = self.cache.get("home", "en")
        self.assertEqual(en_data["title"], "Home")
    
    def test_cache_overwrite(self):
        """Тест перезаписи данных в кэше"""
        # Первое сохранение
        self.cache.set("home", "ru", {"title": "Старый заголовок"})
        
        # Перезапись
        new_data = {"title": "Новый заголовок"}
        self.cache.set("home", "ru", new_data)
        
        # Проверка
        result = self.cache.get("home", "ru")
        self.assertEqual(result["title"], "Новый заголовок")
    
    def test_cache_clear(self):
        """Тест очистки кэша"""
        # Сохранение данных
        self.cache.set("home", "ru", {"title": "Test"})
        
        # Проверка наличия
        result = self.cache.get("home", "ru")
        self.assertIsNotNone(result)
        
        # Очистка
        self.cache.clear()
        
        # Проверка отсутствия
        result = self.cache.get("home", "ru")
        self.assertIsNone(result)
    
    def test_cache_clear_page(self):
        """Тест очистки кэша для конкретной страницы"""
        # Сохранение данных для разных страниц
        self.cache.set("home", "ru", {"title": "Главная"})
        self.cache.set("about", "ru", {"title": "О нас"})
        
        # Очистка только для home
        self.cache.clear_page("home")
        
        # home должен быть очищен
        home_result = self.cache.get("home", "ru")
        self.assertIsNone(home_result)
        
        # about должен остаться
        about_result = self.cache.get("about", "ru")
        self.assertIsNotNone(about_result)
    
    def test_cache_clear_language(self):
        """Тест очистки кэша для конкретного языка"""
        # Сохранение данных для разных языков
        self.cache.set("home", "ru", {"title": "Главная"})
        self.cache.set("home", "en", {"title": "Home"})
        
        # Очистка только для ru
        self.cache.clear_language("ru")
        
        # ru должен быть очищен
        ru_result = self.cache.get("home", "ru")
        self.assertIsNone(ru_result)
        
        # en должен остаться
        en_result = self.cache.get("home", "en")
        self.assertIsNotNone(en_result)
    
    def test_cache_thread_safety(self):
        """Тест потокобезопасности кэша"""
        results = []
        errors = []
        
        def worker(thread_id):
            try:
                # Каждый поток работает с разными ключами
                for i in range(10):
                    key = f"page_{thread_id}_{i}"
                    data = {"title": f"Title {thread_id}_{i}"}
                    
                    # Сохранение
                    self.cache.set(key, "ru", data)
                    
                    # Получение
                    result = self.cache.get(key, "ru")
                    if result:
                        results.append(result["title"])
                    
                    time.sleep(0.001)  # Небольшая задержка
            except Exception as e:
                errors.append(e)
        
        # Запуск нескольких потоков
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Ожидание завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Проверка отсутствия ошибок
        self.assertEqual(len(errors), 0, f"Ошибки в потоках: {errors}")
        
        # Проверка корректности результатов
        self.assertEqual(len(results), 50)  # 5 потоков * 10 итераций
    
    def test_cache_memory_usage(self):
        """Тест использования памяти кэшем"""
        # Сохранение большого количества данных
        for i in range(100):
            large_data = {"title": "A" * 1000, "content": "B" * 1000}
            self.cache.set(f"page_{i}", "ru", large_data)
        
        # Проверка, что все данные доступны
        for i in range(100):
            result = self.cache.get(f"page_{i}", "ru")
            self.assertIsNotNone(result)
            self.assertEqual(len(result["title"]), 1000)
    
    def test_cache_invalidation(self):
        """Тест инвалидации кэша"""
        # Сохранение данных
        self.cache.set("home", "ru", {"title": "Test"})
        
        # Проверка наличия
        result = self.cache.get("home", "ru")
        self.assertIsNotNone(result)
        
        # Инвалидация
        self.cache.invalidate("home", "ru")
        
        # Проверка отсутствия
        result = self.cache.get("home", "ru")
        self.assertIsNone(result)


class TestSEOCache(unittest.TestCase):
    """Тесты для SEOCache"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.cache = SEOCache(default_ttl=1)  # Короткий TTL для тестов
    
    def test_seo_cache_basic_operations(self):
        """Тест базовых операций SEO кэша"""
        # Пустой кэш
        result = self.cache.get("home", "ru")
        self.assertIsNone(result)
        
        # Сохранение SEO данных
        seo_data = {
            "title": "Главная страница",
            "description": "Описание главной страницы",
            "keywords": "ключевые, слова"
        }
        self.cache.set("home", "ru", seo_data)
        
        # Получение данных
        result = self.cache.get("home", "ru")
        self.assertEqual(result, seo_data)
    
    def test_seo_cache_ttl_expiration(self):
        """Тест истечения TTL для SEO кэша"""
        # Сохранение с коротким TTL
        seo_data = {"title": "Test SEO"}
        self.cache.set("home", "ru", seo_data, ttl=0.1)
        
        # Данные должны быть доступны сразу
        result = self.cache.get("home", "ru")
        self.assertEqual(result, seo_data)
        
        # Ждем истечения TTL
        time.sleep(0.2)
        
        # Данные должны исчезнуть
        result = self.cache.get("home", "ru")
        self.assertIsNone(result)
    
    def test_seo_cache_different_pages_languages(self):
        """Тест SEO кэша для разных страниц и языков"""
        # Разные страницы и языки
        test_cases = [
            ("home", "ru", {"title": "Главная"}),
            ("home", "en", {"title": "Home"}),
            ("about", "ru", {"title": "О нас"}),
            ("about", "en", {"title": "About"})
        ]
        
        # Сохранение всех данных
        for page, lang, data in test_cases:
            self.cache.set(page, lang, data)
        
        # Проверка всех данных
        for page, lang, expected_data in test_cases:
            result = self.cache.get(page, lang)
            self.assertEqual(result, expected_data)
    
    def test_seo_cache_clear(self):
        """Тест очистки SEO кэша"""
        # Сохранение данных
        self.cache.set("home", "ru", {"title": "Test"})
        self.cache.set("about", "en", {"title": "About"})
        
        # Очистка
        self.cache.clear()
        
        # Проверка отсутствия данных
        self.assertIsNone(self.cache.get("home", "ru"))
        self.assertIsNone(self.cache.get("about", "en"))


class TestCacheIntegration(unittest.TestCase):
    """Интеграционные тесты кэша"""
    
    def test_cache_performance(self):
        """Тест производительности кэша"""
        cache = TextCache(default_ttl=60)
        
        # Измерение времени операций
        start_time = time.time()
        
        # Множественные операции
        for i in range(1000):
            data = {"title": f"Title {i}"}
            cache.set(f"page_{i}", "ru", data)
            result = cache.get(f"page_{i}", "ru")
            self.assertIsNotNone(result)
        
        end_time = time.time()
        
        # Операции должны быть быстрыми
        duration = end_time - start_time
        self.assertLess(duration, 1.0, f"Кэш слишком медленный: {duration} сек")
    
    def test_cache_concurrent_access(self):
        """Тест конкурентного доступа к кэшу"""
        cache = TextCache(default_ttl=60)
        results = []
        
        def reader(thread_id):
            for i in range(50):
                result = cache.get(f"shared_page", "ru")
                if result:
                    results.append(f"thread_{thread_id}_read_{result['title']}")
                time.sleep(0.001)
        
        def writer(thread_id):
            for i in range(50):
                data = {"title": f"data_{thread_id}_{i}"}
                cache.set(f"shared_page", "ru", data)
                time.sleep(0.001)
        
        # Запуск читателей и писателей
        threads = []
        
        # 3 писателя
        for i in range(3):
            thread = threading.Thread(target=writer, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 2 читателя
        for i in range(2):
            thread = threading.Thread(target=reader, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Ожидание завершения
        for thread in threads:
            thread.join()
        
        # Проверка, что не было ошибок
        self.assertGreater(len(results), 0)
    
    def test_cache_memory_cleanup(self):
        """Тест очистки памяти при истечении TTL"""
        cache = TextCache(default_ttl=0.1)  # Очень короткий TTL
        
        # Заполнение кэша
        for i in range(100):
            cache.set(f"page_{i}", "ru", {"title": f"Title {i}"})
        
        # Ожидание истечения TTL
        time.sleep(0.2)
        
        # Проверка, что все данные исчезли
        for i in range(100):
            result = cache.get(f"page_{i}", "ru")
            self.assertIsNone(result, f"Данные для page_{i} должны быть удалены")


if __name__ == "__main__":
    # Настройка тестирования
    unittest.main(verbosity=2)
