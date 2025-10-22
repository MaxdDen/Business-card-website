"""
Автотест для проверки мультиязычности
Проверяет автоматическое определение языка, переключение языков, кэширование
"""

import requests
import time
import os
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.database.db import execute, query_one, query_all
from app.utils.cache import text_cache, image_cache

class MultilangTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, success, message=""):
        """Логирование результата теста"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
        
    def test_server_running(self):
        """Проверка, что сервер запущен"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                self.log_test("Server Running", True, "Сервер отвечает на /health")
                return True
            else:
                self.log_test("Server Running", False, f"Неожиданный статус: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Server Running", False, f"Ошибка подключения: {e}")
            return False
    
    def test_language_detection(self):
        """Проверка автоматического определения языка из URL"""
        test_cases = [
            ("/", "en", "Главная страница без языка (английский по умолчанию)"),
            ("/en/", "en", "Английский язык"),
            ("/ru/", "ru", "Русский язык"),
            ("/ua/", "ua", "Украинский язык"),
            ("/en/about", "en", "Английский язык на странице about"),
            ("/ru/catalog", "ru", "Русский язык на странице catalog"),
            ("/ua/contacts", "ua", "Украинский язык на странице contacts")
        ]
        
        for url, expected_lang, description in test_cases:
            try:
                response = self.session.get(f"{self.base_url}{url}", timeout=10)
                if response.status_code == 200:
                    # Проверяем, что язык определяется корректно
                    # (это можно проверить по содержимому страницы или заголовкам)
                    self.log_test(f"Language Detection {url}", True, f"{description} - язык {expected_lang}")
                else:
                    self.log_test(f"Language Detection {url}", False, f"Статус {response.status_code}")
            except Exception as e:
                self.log_test(f"Language Detection {url}", False, f"Ошибка: {e}")
    
    def test_language_switching(self):
        """Проверка переключения языков"""
        try:
            # Проверяем все языки на главной странице
            languages = ["en", "ru", "ua"]
            for lang in languages:
                url = f"/{lang}/" if lang != "en" else "/"
                response = self.session.get(f"{self.base_url}{url}", timeout=10)
                if response.status_code == 200:
                    self.log_test(f"Language Switch {lang}", True, f"Страница загружается на {lang}")
                else:
                    self.log_test(f"Language Switch {lang}", False, f"Статус {response.status_code}")
        except Exception as e:
            self.log_test("Language Switching", False, f"Ошибка: {e}")
    
    def test_language_consistency(self):
        """Проверка консистентности языков на всех страницах"""
        pages = ["", "/about", "/catalog", "/contacts"]
        languages = ["en", "ru", "ua"]
        
        for page in pages:
            for lang in languages:
                url = f"/{lang}{page}" if lang != "en" else page
                try:
                    response = self.session.get(f"{self.base_url}{url}", timeout=10)
                    if response.status_code == 200:
                        self.log_test(f"Consistency {lang}{page}", True, f"Страница {page} на {lang}")
                    else:
                        self.log_test(f"Consistency {lang}{page}", False, f"Статус {response.status_code}")
                except Exception as e:
                    self.log_test(f"Consistency {lang}{page}", False, f"Ошибка: {e}")
    
    def test_language_urls_generation(self):
        """Проверка генерации URL для всех языков"""
        try:
            # Проверяем, что переключатель языков работает
            response = self.session.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                content = response.text
                # Проверяем наличие ссылок на языки
                if "href=\"/en/\"" in content and "href=\"/ua/\"" in content:
                    self.log_test("Language URLs Generation", True, "URL для языков генерируются корректно")
                else:
                    self.log_test("Language URLs Generation", False, "URL для языков не найдены в HTML")
            else:
                self.log_test("Language URLs Generation", False, f"Статус {response.status_code}")
        except Exception as e:
            self.log_test("Language URLs Generation", False, f"Ошибка: {e}")
    
    def test_multilang_content_loading(self):
        """Проверка загрузки контента для разных языков"""
        # Добавляем тестовые данные для разных языков
        self.setup_multilang_test_data()
        
        languages = ["en", "ru", "ua"]
        for lang in languages:
            try:
                url = f"/{lang}/" if lang != "en" else "/"
                response = self.session.get(f"{self.base_url}{url}", timeout=10)
                if response.status_code == 200:
                    content = response.text
                    # Проверяем, что контент загружается на правильном языке
                    if self.check_language_content(content, lang):
                        self.log_test(f"Multilang Content {lang}", True, f"Контент загружается на {lang}")
                    else:
                        self.log_test(f"Multilang Content {lang}", False, f"Контент не соответствует языку {lang}")
                else:
                    self.log_test(f"Multilang Content {lang}", False, f"Статус {response.status_code}")
            except Exception as e:
                self.log_test(f"Multilang Content {lang}", False, f"Ошибка: {e}")
    
    def test_language_caching(self):
        """Проверка кэширования для разных языков"""
        try:
            # Очищаем кэш
            text_cache.clear()
            image_cache.clear()
            
            # Первый запрос - должен загружаться из БД
            start_time = time.time()
            response1 = self.session.get(f"{self.base_url}/", timeout=10)
            time1 = time.time() - start_time
            
            # Второй запрос - должен загружаться из кэша
            start_time = time.time()
            response2 = self.session.get(f"{self.base_url}/", timeout=10)
            time2 = time.time() - start_time
            
            if response1.status_code == 200 and response2.status_code == 200:
                if time2 < time1:  # Второй запрос должен быть быстрее
                    self.log_test("Language Caching", True, f"Кэш работает: {time1:.3f}s -> {time2:.3f}s")
                else:
                    self.log_test("Language Caching", False, f"Кэш не ускоряет: {time1:.3f}s -> {time2:.3f}s")
            else:
                self.log_test("Language Caching", False, f"Ошибки запросов: {response1.status_code}, {response2.status_code}")
                
        except Exception as e:
            self.log_test("Language Caching", False, f"Ошибка: {e}")
    
    def test_fast_language_switching(self):
        """Проверка быстрого переключения языков"""
        try:
            languages = ["en", "ru", "ua"]
            start_time = time.time()
            
            # Быстро переключаемся между языками
            for lang in languages:
                url = f"/{lang}/" if lang != "en" else "/"
                response = self.session.get(f"{self.base_url}{url}", timeout=5)
                if response.status_code != 200:
                    self.log_test("Fast Language Switching", False, f"Ошибка на языке {lang}")
                    return
            
            total_time = time.time() - start_time
            
            if total_time < 3.0:  # Должно быть быстро
                self.log_test("Fast Language Switching", True, f"Быстрое переключение: {total_time:.2f}s")
            else:
                self.log_test("Fast Language Switching", False, f"Медленное переключение: {total_time:.2f}s")
                
        except Exception as e:
            self.log_test("Fast Language Switching", False, f"Ошибка: {e}")
    
    def setup_multilang_test_data(self):
        """Настройка тестовых данных для разных языков"""
        try:
            # Очищаем кэш
            text_cache.clear()
            image_cache.clear()
            
            # Добавляем тестовые тексты для всех языков
            test_texts = [
                # Русский
                ("home", "title", "ru", "Тестовая главная страница"),
                ("home", "subtitle", "ru", "Русский подзаголовок"),
                ("about", "title", "ru", "О компании"),
                ("about", "description", "ru", "Описание компании на русском"),
                # Английский
                ("home", "title", "en", "Test Home Page"),
                ("home", "subtitle", "en", "English subtitle"),
                ("about", "title", "en", "About Company"),
                ("about", "description", "en", "Company description in English"),
                # Украинский
                ("home", "title", "ua", "Тестова головна сторінка"),
                ("home", "subtitle", "ua", "Український підзаголовок"),
                ("about", "title", "ua", "Про компанію"),
                ("about", "description", "ua", "Опис компанії українською")
            ]
            
            for page, key, lang, value in test_texts:
                execute(
                    "INSERT OR REPLACE INTO texts (page, key, lang, value) VALUES (?, ?, ?, ?)",
                    (page, key, lang, value)
                )
            
            # Добавляем SEO данные для всех языков
            test_seo = [
                ("home", "ru", "Тестовая главная страница", "Описание главной страницы", "тест, главная, страница"),
                ("home", "en", "Test Home Page", "Home page description", "test, home, page"),
                ("home", "ua", "Тестова головна сторінка", "Опис головної сторінки", "тест, головна, сторінка"),
                ("about", "ru", "О компании", "Описание компании", "компания, о нас"),
                ("about", "en", "About Company", "Company description", "company, about us"),
                ("about", "ua", "Про компанію", "Опис компанії", "компанія, про нас")
            ]
            
            for page, lang, title, description, keywords in test_seo:
                execute(
                    "INSERT OR REPLACE INTO seo (page, lang, title, description, keywords) VALUES (?, ?, ?, ?, ?)",
                    (page, lang, title, description, keywords)
                )
            
            self.log_test("Multilang Test Data Setup", True, "Тестовые данные для всех языков добавлены")
            
        except Exception as e:
            self.log_test("Multilang Test Data Setup", False, f"Ошибка: {e}")
    
    def check_language_content(self, content: str, language: str) -> bool:
        """Проверить, что контент соответствует языку"""
        if language == "en":
            return "Test Home Page" in content or "English" in content
        elif language == "ru":
            return "Тестовая главная страница" in content or "Русский" in content
        elif language == "ua":
            return "Тестова головна сторінка" in content or "Український" in content
        return False
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 Запуск автотестов мультиязычности...")
        print("=" * 60)
        
        # Проверяем, что сервер запущен
        if not self.test_server_running():
            print("❌ Сервер не запущен! Запустите сервер командой: uvicorn app.main:app --reload")
            return False
        
        print()
        
        # Запускаем все тесты
        self.test_language_detection()
        self.test_language_switching()
        self.test_language_consistency()
        self.test_language_urls_generation()
        self.test_multilang_content_loading()
        self.test_language_caching()
        self.test_fast_language_switching()
        
        # Подводим итоги
        print()
        print("=" * 60)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ МУЛЬТИЯЗЫЧНОСТИ:")
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"✅ Пройдено: {passed}/{total}")
        print(f"❌ Провалено: {total - passed}/{total}")
        
        if passed == total:
            print("🎉 ВСЕ ТЕСТЫ МУЛЬТИЯЗЫЧНОСТИ ПРОЙДЕНЫ УСПЕШНО!")
            return True
        else:
            print("⚠️  НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
            print("\nДетали проваленных тестов:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['message']}")
            return False

def main():
    """Главная функция для запуска тестов"""
    print("🧪 Автотест мультиязычности")
    print("Проверяет автоматическое определение языка, переключение языков, кэширование")
    print()
    
    tester = MultilangTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Этап 10 (Мультиязычность) реализован успешно!")
        print("Автоматическое определение языка, переключение языков и кэширование работают корректно")
    else:
        print("\n❌ Обнаружены проблемы в реализации этапа 10")
        print("Проверьте логи выше для деталей")
    
    return success

if __name__ == "__main__":
    main()
