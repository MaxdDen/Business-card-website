"""
Автотест для проверки публичного сайта
Проверяет все публичные роуты, мультиязычность, загрузку контента из БД
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

class PublicSiteTester:
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
    
    def test_public_routes(self):
        """Проверка основных публичных роутов"""
        routes = [
            ("/", "Главная страница"),
            ("/about", "Страница о компании"),
            ("/catalog", "Страница каталога"),
            ("/contacts", "Страница контактов")
        ]
        
        for route, description in routes:
            try:
                response = self.session.get(f"{self.base_url}{route}", timeout=10)
                if response.status_code == 200:
                    self.log_test(f"Route {route}", True, f"{description} загружается")
                else:
                    self.log_test(f"Route {route}", False, f"Статус {response.status_code}")
            except Exception as e:
                self.log_test(f"Route {route}", False, f"Ошибка: {e}")
    
    def test_multilang_routes(self):
        """Проверка мультиязычных роутов"""
        languages = ["en", "ua", "ru"]
        pages = ["", "/about", "/catalog", "/contacts"]
        
        for lang in languages:
            for page in pages:
                route = f"/{lang}{page}" if page else f"/{lang}/"
                try:
                    response = self.session.get(f"{self.base_url}{route}", timeout=10)
                    if response.status_code == 200:
                        self.log_test(f"Multilang {route}", True, f"Язык {lang} работает")
                    else:
                        self.log_test(f"Multilang {route}", False, f"Статус {response.status_code}")
                except Exception as e:
                    self.log_test(f"Multilang {route}", False, f"Ошибка: {e}")
    
    def test_content_loading(self):
        """Проверка загрузки контента из БД"""
        # Добавляем тестовые данные в БД
        self.setup_test_data()
        
        # Проверяем загрузку текстов
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                content = response.text
                if "Тестовая главная страница" in content:
                    self.log_test("Content Loading", True, "Тексты загружаются из БД")
                else:
                    self.log_test("Content Loading", False, "Тексты не найдены в HTML")
            else:
                self.log_test("Content Loading", False, f"Статус {response.status_code}")
        except Exception as e:
            self.log_test("Content Loading", False, f"Ошибка: {e}")
    
    def test_seo_integration(self):
        """Проверка интеграции SEO тегов"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                content = response.text
                seo_elements = [
                    '<title>',
                    '<meta name="description"',
                    '<meta name="keywords"'
                ]
                
                found_elements = sum(1 for element in seo_elements if element in content)
                if found_elements >= 2:
                    self.log_test("SEO Integration", True, f"Найдено {found_elements} SEO элементов")
                else:
                    self.log_test("SEO Integration", False, f"Найдено только {found_elements} SEO элементов")
            else:
                self.log_test("SEO Integration", False, f"Статус {response.status_code}")
        except Exception as e:
            self.log_test("SEO Integration", False, f"Ошибка: {e}")
    
    def test_image_loading(self):
        """Проверка загрузки изображений"""
        # Добавляем тестовое изображение
        self.setup_test_images()
        
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                content = response.text
                if "/uploads/" in content:
                    self.log_test("Image Loading", True, "Изображения загружаются")
                else:
                    self.log_test("Image Loading", False, "Пути к изображениям не найдены")
            else:
                self.log_test("Image Loading", False, f"Статус {response.status_code}")
        except Exception as e:
            self.log_test("Image Loading", False, f"Ошибка: {e}")
    
    def test_theme_switching(self):
        """Проверка переключения темы"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                content = response.text
                if "data-theme" in content and "toggleTheme" in content:
                    self.log_test("Theme Switching", True, "Переключение темы реализовано")
                else:
                    self.log_test("Theme Switching", False, "Функционал переключения темы не найден")
            else:
                self.log_test("Theme Switching", False, f"Статус {response.status_code}")
        except Exception as e:
            self.log_test("Theme Switching", False, f"Ошибка: {e}")
    
    def test_language_switching(self):
        """Проверка переключения языков"""
        try:
            # Проверяем русскую версию
            response_ru = self.session.get(f"{self.base_url}/ru/", timeout=10)
            # Проверяем английскую версию
            response_en = self.session.get(f"{self.base_url}/en/", timeout=10)
            
            if response_ru.status_code == 200 and response_en.status_code == 200:
                self.log_test("Language Switching", True, "Переключение языков работает")
            else:
                self.log_test("Language Switching", False, f"RU: {response_ru.status_code}, EN: {response_en.status_code}")
        except Exception as e:
            self.log_test("Language Switching", False, f"Ошибка: {e}")
    
    def setup_test_data(self):
        """Настройка тестовых данных в БД"""
        try:
            # Очищаем кэш
            text_cache.clear()
            image_cache.clear()
            
            # Добавляем тестовые тексты
            test_texts = [
                ("home", "title", "ru", "Тестовая главная страница"),
                ("home", "subtitle", "ru", "Тестовый подзаголовок"),
                ("home", "description", "ru", "Тестовое описание главной страницы"),
                ("home", "cta_text", "ru", "Связаться с нами"),
                ("about", "title", "ru", "О компании"),
                ("about", "description", "ru", "Описание компании"),
                ("catalog", "title", "ru", "Каталог товаров"),
                ("catalog", "description", "ru", "Описание каталога"),
                ("contacts", "title", "ru", "Контакты"),
                ("contacts", "phone", "ru", "+7 (999) 123-45-67"),
                ("contacts", "address", "ru", "Москва, ул. Тестовая, д. 1")
            ]
            
            for page, key, lang, value in test_texts:
                execute(
                    "INSERT OR REPLACE INTO texts (page, key, lang, value) VALUES (?, ?, ?, ?)",
                    (page, key, lang, value)
                )
            
            # Добавляем тестовые SEO данные
            test_seo = [
                ("home", "ru", "Тестовая главная страница", "Описание главной страницы", "тест, главная, страница"),
                ("about", "ru", "О компании", "Описание компании", "компания, о нас"),
                ("catalog", "ru", "Каталог товаров", "Описание каталога", "каталог, товары"),
                ("contacts", "ru", "Контакты", "Контактная информация", "контакты, связь")
            ]
            
            for page, lang, title, description, keywords in test_seo:
                execute(
                    "INSERT OR REPLACE INTO seo (page, lang, title, description, keywords) VALUES (?, ?, ?, ?, ?)",
                    (page, lang, title, description, keywords)
                )
            
            self.log_test("Test Data Setup", True, "Тестовые данные добавлены в БД")
            
        except Exception as e:
            self.log_test("Test Data Setup", False, f"Ошибка: {e}")
    
    def setup_test_images(self):
        """Настройка тестовых изображений"""
        try:
            # Создаем директории для загрузок
            os.makedirs("uploads/originals", exist_ok=True)
            os.makedirs("uploads/optimized", exist_ok=True)
            
            # Добавляем тестовые записи об изображениях
            test_images = [
                ("logo", "test-logo.webp", "test-logo-original.jpg", 0),
                ("background", "test-bg.webp", "test-bg-original.jpg", 0),
                ("slider", "test-slide1.webp", "test-slide1-original.jpg", 1),
                ("slider", "test-slide2.webp", "test-slide2-original.jpg", 2)
            ]
            
            for img_type, path, original_path, order in test_images:
                execute(
                    "INSERT OR REPLACE INTO images (type, path, original_path, order) VALUES (?, ?, ?, ?)",
                    (img_type, path, original_path, order)
                )
            
            self.log_test("Test Images Setup", True, "Тестовые изображения добавлены в БД")
            
        except Exception as e:
            self.log_test("Test Images Setup", False, f"Ошибка: {e}")
    
    def test_cache_functionality(self):
        """Проверка работы кэширования"""
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
                    self.log_test("Cache Functionality", True, f"Кэш работает: {time1:.3f}s -> {time2:.3f}s")
                else:
                    self.log_test("Cache Functionality", False, f"Кэш не ускоряет: {time1:.3f}s -> {time2:.3f}s")
            else:
                self.log_test("Cache Functionality", False, f"Ошибки запросов: {response1.status_code}, {response2.status_code}")
                
        except Exception as e:
            self.log_test("Cache Functionality", False, f"Ошибка: {e}")
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 Запуск автотестов публичного сайта...")
        print("=" * 60)
        
        # Проверяем, что сервер запущен
        if not self.test_server_running():
            print("❌ Сервер не запущен! Запустите сервер командой: uvicorn app.main:app --reload")
            return False
        
        print()
        
        # Запускаем все тесты
        self.test_public_routes()
        self.test_multilang_routes()
        self.test_content_loading()
        self.test_seo_integration()
        self.test_image_loading()
        self.test_theme_switching()
        self.test_language_switching()
        self.test_cache_functionality()
        
        # Подводим итоги
        print()
        print("=" * 60)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"✅ Пройдено: {passed}/{total}")
        print(f"❌ Провалено: {total - passed}/{total}")
        
        if passed == total:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
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
    print("🧪 Автотест публичного сайта")
    print("Проверяет все публичные роуты, мультиязычность, загрузку контента из БД")
    print()
    
    tester = PublicSiteTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Этап 9 (Публичный сайт) реализован успешно!")
        print("Публичные страницы работают с мультиязычностью и загрузкой контента из БД")
    else:
        print("\n❌ Обнаружены проблемы в реализации этапа 9")
        print("Проверьте логи выше для деталей")
    
    return success

if __name__ == "__main__":
    main()
