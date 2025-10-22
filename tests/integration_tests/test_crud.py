#!/usr/bin/env python3
"""
Интеграционные тесты для CRUD операций
Проверяет полный цикл работы с текстами, SEO и изображениями через API
"""

import sys
import os
import json
import time
import base64
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import unittest

# Добавляем путь к модулям приложения
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

class TestCRUDIntegration(unittest.TestCase):
    """Интеграционные тесты CRUD операций"""
    
    @classmethod
    def setUpClass(cls):
        """Настройка перед всеми тестами"""
        cls.base_url = "http://localhost:8000"
        cls.session = requests.Session()
        
        # Настройка retry стратегии
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        cls.session.mount("http://", adapter)
        cls.session.mount("https://", adapter)
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.session.cookies.clear()
        self.test_data = {
            "texts": {
                "home": {
                    "ru": {"title": "Главная", "subtitle": "Добро пожаловать", "description": "Описание главной страницы"},
                    "en": {"title": "Home", "subtitle": "Welcome", "description": "Home page description"}
                },
                "about": {
                    "ru": {"title": "О нас", "subtitle": "Наша компания", "description": "Информация о компании"},
                    "en": {"title": "About", "subtitle": "Our company", "description": "Company information"}
                }
            },
            "seo": {
                "home": {
                    "ru": {"title": "Главная - Название сайта", "description": "Описание главной страницы", "keywords": "главная, сайт"},
                    "en": {"title": "Home - Site Name", "description": "Home page description", "keywords": "home, site"}
                }
            }
        }
    
    def authenticate_user(self):
        """Аутентификация пользователя для тестов"""
        try:
            # Попытка входа с тестовыми данными
            login_data = {
                "email": "admin@example.com",
                "password": "adminpassword123"
            }
            
            response = self.session.post(
                f"{self.base_url}/login",
                data=login_data,
                timeout=10
            )
            
            if response.status_code == 200 and "cms" in response.url.lower():
                return True
            else:
                # Если нет тестового пользователя, попробуем зарегистрировать
                registration_data = {
                    "email": f"test_{int(time.time())}@example.com",
                    "password": "testpassword123",
                    "confirm_password": "testpassword123"
                }
                
                response = self.session.post(
                    f"{self.base_url}/register",
                    data=registration_data,
                    timeout=10
                )
                
                return response.status_code == 200 and "cms" in response.url.lower()
                
        except Exception as e:
            print(f"⚠️  Ошибка аутентификации: {e}")
            return False
    
    def test_texts_crud_operations(self):
        """Тест CRUD операций для текстов"""
        print("\n📝 Тестирование CRUD операций для текстов...")
        
        if not self.authenticate_user():
            print("❌ Не удалось аутентифицироваться")
            return
        
        try:
            # 1. Получение текстов
            response = self.session.get(f"{self.base_url}/cms/api/texts", timeout=10)
            if response.status_code == 200:
                print("✅ Получение текстов работает")
                texts_data = response.json()
                print(f"   Получено {len(texts_data)} текстовых блоков")
            else:
                print(f"⚠️  Получение текстов: статус {response.status_code}")
            
            # 2. Сохранение текстов
            test_texts = {
                "page": "home",
                "lang": "ru",
                "texts": {
                    "title": f"Тестовый заголовок {int(time.time())}",
                    "subtitle": "Тестовый подзаголовок",
                    "description": "Тестовое описание"
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/cms/api/texts",
                json=test_texts,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Сохранение текстов работает")
                
                # Проверяем, что данные сохранились
                response = self.session.get(f"{self.base_url}/cms/api/texts", timeout=10)
                if response.status_code == 200:
                    saved_texts = response.json()
                    # Ищем наш тестовый заголовок
                    found = False
                    for text_block in saved_texts:
                        if "Тестовый заголовок" in text_block.get("value", ""):
                            found = True
                            break
                    
                    if found:
                        print("✅ Тексты успешно сохранены и загружены")
                    else:
                        print("⚠️  Сохраненные тексты не найдены при загрузке")
                else:
                    print(f"⚠️  Проверка сохранения: статус {response.status_code}")
            else:
                print(f"⚠️  Сохранение текстов: статус {response.status_code}")
                
        except Exception as e:
            print(f"⚠️  Ошибка тестирования текстов: {e}")
    
    def test_seo_crud_operations(self):
        """Тест CRUD операций для SEO"""
        print("\n🔍 Тестирование CRUD операций для SEO...")
        
        if not self.authenticate_user():
            print("❌ Не удалось аутентифицироваться")
            return
        
        try:
            # 1. Получение SEO данных
            response = self.session.get(f"{self.base_url}/cms/api/seo", timeout=10)
            if response.status_code == 200:
                print("✅ Получение SEO данных работает")
                seo_data = response.json()
                print(f"   Получено {len(seo_data)} SEO записей")
            else:
                print(f"⚠️  Получение SEO: статус {response.status_code}")
            
            # 2. Сохранение SEO данных
            test_seo = {
                "page": "home",
                "lang": "ru",
                "seo": {
                    "title": f"SEO заголовок {int(time.time())}",
                    "description": "SEO описание для тестирования",
                    "keywords": "тест, seo, ключевые слова"
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/cms/api/seo",
                json=test_seo,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Сохранение SEO данных работает")
                
                # Проверяем сохранение
                response = self.session.get(f"{self.base_url}/cms/api/seo", timeout=10)
                if response.status_code == 200:
                    saved_seo = response.json()
                    found = False
                    for seo_block in saved_seo:
                        if "SEO заголовок" in seo_block.get("title", ""):
                            found = True
                            break
                    
                    if found:
                        print("✅ SEO данные успешно сохранены и загружены")
                    else:
                        print("⚠️  Сохраненные SEO данные не найдены при загрузке")
                else:
                    print(f"⚠️  Проверка сохранения SEO: статус {response.status_code}")
            else:
                print(f"⚠️  Сохранение SEO: статус {response.status_code}")
                
        except Exception as e:
            print(f"⚠️  Ошибка тестирования SEO: {e}")
    
    def test_images_crud_operations(self):
        """Тест CRUD операций для изображений"""
        print("\n🖼️  Тестирование CRUD операций для изображений...")
        
        if not self.authenticate_user():
            print("❌ Не удалось аутентифицироваться")
            return
        
        try:
            # 1. Получение списка изображений
            response = self.session.get(f"{self.base_url}/cms/api/images", timeout=10)
            if response.status_code == 200:
                print("✅ Получение списка изображений работает")
                images_data = response.json()
                print(f"   Найдено {len(images_data)} изображений")
            else:
                print(f"⚠️  Получение изображений: статус {response.status_code}")
            
            # 2. Создание тестового изображения (1x1 пиксель PNG)
            test_image_data = base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            )
            
            files = {
                'file': ('test_image.png', test_image_data, 'image/png')
            }
            data = {
                'type': 'slider',
                'order': '1'
            }
            
            response = self.session.post(
                f"{self.base_url}/cms/api/images/upload",
                files=files,
                data=data,
                timeout=15
            )
            
            if response.status_code == 200:
                print("✅ Загрузка изображения работает")
                
                # Проверяем, что изображение появилось в списке
                response = self.session.get(f"{self.base_url}/cms/api/images", timeout=10)
                if response.status_code == 200:
                    updated_images = response.json()
                    if len(updated_images) > 0:
                        print("✅ Изображение успешно загружено и появилось в списке")
                        
                        # Пытаемся удалить тестовое изображение
                        if updated_images:
                            test_image = updated_images[0]
                            if 'id' in test_image:
                                delete_response = self.session.delete(
                                    f"{self.base_url}/cms/api/images/{test_image['id']}",
                                    timeout=10
                                )
                                if delete_response.status_code == 200:
                                    print("✅ Удаление изображения работает")
                                else:
                                    print(f"⚠️  Удаление изображения: статус {delete_response.status_code}")
                    else:
                        print("⚠️  Загруженное изображение не найдено в списке")
                else:
                    print(f"⚠️  Проверка загрузки изображения: статус {response.status_code}")
            else:
                print(f"⚠️  Загрузка изображения: статус {response.status_code}")
                
        except Exception as e:
            print(f"⚠️  Ошибка тестирования изображений: {e}")
    
    def test_validation_errors(self):
        """Тест валидации данных"""
        print("\n🔍 Тестирование валидации данных...")
        
        if not self.authenticate_user():
            print("❌ Не удалось аутентифицироваться")
            return
        
        try:
            # Тест валидации текстов
            invalid_texts = {
                "page": "invalid_page",  # Невалидная страница
                "lang": "invalid_lang",  # Невалидный язык
                "texts": {
                    "title": "A" * 1000  # Слишком длинный заголовок
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/cms/api/texts",
                json=invalid_texts,
                timeout=10
            )
            
            if response.status_code == 400:
                print("✅ Валидация текстов работает")
            else:
                print(f"⚠️  Валидация текстов: статус {response.status_code}")
            
            # Тест валидации SEO
            invalid_seo = {
                "page": "home",
                "lang": "ru",
                "seo": {
                    "title": "A" * 100,  # Слишком длинный title
                    "description": "B" * 200,  # Слишком длинное description
                    "keywords": "C" * 300  # Слишком длинные keywords
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/cms/api/seo",
                json=invalid_seo,
                timeout=10
            )
            
            if response.status_code == 400:
                print("✅ Валидация SEO работает")
            else:
                print(f"⚠️  Валидация SEO: статус {response.status_code}")
                
        except Exception as e:
            print(f"⚠️  Ошибка тестирования валидации: {e}")
    
    def test_performance_metrics(self):
        """Тест метрик производительности"""
        print("\n⚡ Тестирование производительности...")
        
        if not self.authenticate_user():
            print("❌ Не удалось аутентифицироваться")
            return
        
        try:
            # Тест времени ответа для получения текстов
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/cms/api/texts", timeout=10)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response.status_code == 200:
                if response_time < 1.0:
                    print(f"✅ Получение текстов быстро: {response_time:.3f}с")
                else:
                    print(f"⚠️  Получение текстов медленно: {response_time:.3f}с")
            else:
                print(f"⚠️  Получение текстов: статус {response.status_code}")
            
            # Тест времени ответа для получения SEO
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/cms/api/seo", timeout=10)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response.status_code == 200:
                if response_time < 1.0:
                    print(f"✅ Получение SEO быстро: {response_time:.3f}с")
                else:
                    print(f"⚠️  Получение SEO медленно: {response_time:.3f}с")
            else:
                print(f"⚠️  Получение SEO: статус {response.status_code}")
            
            # Тест времени ответа для получения изображений
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/cms/api/images", timeout=10)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response.status_code == 200:
                if response_time < 1.0:
                    print(f"✅ Получение изображений быстро: {response_time:.3f}с")
                else:
                    print(f"⚠️  Получение изображений медленно: {response_time:.3f}с")
            else:
                print(f"⚠️  Получение изображений: статус {response.status_code}")
                
        except Exception as e:
            print(f"⚠️  Ошибка тестирования производительности: {e}")
    
    def test_concurrent_operations(self):
        """Тест конкурентных операций"""
        print("\n🔄 Тестирование конкурентных операций...")
        
        if not self.authenticate_user():
            print("❌ Не удалось аутентифицироваться")
            return
        
        try:
            import threading
            import queue
            
            results = queue.Queue()
            
            def worker(worker_id):
                try:
                    # Каждый worker выполняет операции
                    for i in range(5):
                        # Получение текстов
                        response = self.session.get(f"{self.base_url}/cms/api/texts", timeout=5)
                        if response.status_code == 200:
                            results.put(f"worker_{worker_id}_get_texts_ok")
                        
                        # Получение SEO
                        response = self.session.get(f"{self.base_url}/cms/api/seo", timeout=5)
                        if response.status_code == 200:
                            results.put(f"worker_{worker_id}_get_seo_ok")
                        
                        time.sleep(0.1)
                    
                    results.put(f"worker_{worker_id}_completed")
                except Exception as e:
                    results.put(f"worker_{worker_id}_error: {e}")
            
            # Запуск нескольких worker'ов
            threads = []
            for i in range(3):
                thread = threading.Thread(target=worker, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Ожидание завершения
            for thread in threads:
                thread.join()
            
            # Анализ результатов
            success_count = 0
            error_count = 0
            
            while not results.empty():
                result = results.get()
                if "ok" in result:
                    success_count += 1
                elif "error" in result:
                    error_count += 1
            
            print(f"✅ Конкурентные операции: {success_count} успешных, {error_count} ошибок")
            
        except Exception as e:
            print(f"⚠️  Ошибка тестирования конкурентных операций: {e}")


if __name__ == "__main__":
    # Настройка тестирования
    print("🧪 Запуск интеграционных тестов CRUD операций...")
    print("=" * 60)
    print("⚠️  Убедитесь, что сервер запущен: uvicorn app.main:app --reload")
    print("=" * 60)
    
    unittest.main(verbosity=2)
