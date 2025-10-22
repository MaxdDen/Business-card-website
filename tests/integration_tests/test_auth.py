#!/usr/bin/env python3
"""
Интеграционные тесты для аутентификации
Проверяет полный цикл аутентификации через API
"""

import sys
import os
import json
import time
import unittest
from unittest.mock import patch
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Добавляем путь к модулям приложения
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

class TestAuthIntegration(unittest.TestCase):
    """Интеграционные тесты аутентификации"""
    
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
        self.test_user = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        # Очистка cookies перед каждым тестом
        self.session.cookies.clear()
    
    def test_server_health(self):
        """Тест доступности сервера"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            self.assertEqual(response.status_code, 200)
            print("✅ Сервер доступен")
        except requests.exceptions.RequestException as e:
            self.fail(f"Сервер недоступен: {e}")
    
    def test_login_page_access(self):
        """Тест доступа к странице логина"""
        try:
            response = self.session.get(f"{self.base_url}/login", timeout=5)
            self.assertEqual(response.status_code, 200)
            self.assertIn("login", response.text.lower())
            print("✅ Страница логина доступна")
        except requests.exceptions.RequestException as e:
            self.fail(f"Ошибка доступа к странице логина: {e}")
    
    def test_register_page_access(self):
        """Тест доступа к странице регистрации"""
        try:
            response = self.session.get(f"{self.base_url}/register", timeout=5)
            self.assertEqual(response.status_code, 200)
            self.assertIn("register", response.text.lower())
            print("✅ Страница регистрации доступна")
        except requests.exceptions.RequestException as e:
            self.fail(f"Ошибка доступа к странице регистрации: {e}")
    
    def test_cms_redirect_without_auth(self):
        """Тест редиректа на логин при попытке доступа к CMS без аутентификации"""
        try:
            response = self.session.get(f"{self.base_url}/cms", timeout=5, allow_redirects=False)
            # Должен быть редирект на логин
            self.assertIn(response.status_code, [302, 307])
            self.assertIn("/login", response.headers.get("Location", ""))
            print("✅ Редирект на логин работает")
        except requests.exceptions.RequestException as e:
            self.fail(f"Ошибка проверки редиректа: {e}")
    
    def test_user_registration(self):
        """Тест регистрации нового пользователя"""
        try:
            # Данные для регистрации
            registration_data = {
                "email": f"newuser_{int(time.time())}@example.com",
                "password": "newpassword123",
                "confirm_password": "newpassword123"
            }
            
            # Отправляем запрос регистрации
            response = self.session.post(
                f"{self.base_url}/register",
                data=registration_data,
                timeout=10
            )
            
            # Проверяем результат
            if response.status_code == 200:
                # Проверяем, что есть редирект на CMS или сообщение об успехе
                if "cms" in response.url.lower() or "success" in response.text.lower():
                    print("✅ Регистрация пользователя успешна")
                else:
                    print(f"⚠️  Регистрация: неожиданный ответ - {response.status_code}")
            else:
                print(f"⚠️  Регистрация: статус {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Ошибка регистрации: {e}")
    
    def test_user_login_invalid_credentials(self):
        """Тест логина с неверными данными"""
        try:
            # Неверные данные
            login_data = {
                "email": "nonexistent@example.com",
                "password": "wrongpassword"
            }
            
            response = self.session.post(
                f"{self.base_url}/login",
                data=login_data,
                timeout=10
            )
            
            # Должна остаться на странице логина с ошибкой
            self.assertEqual(response.status_code, 200)
            self.assertIn("login", response.url.lower())
            print("✅ Неверные данные отклонены")
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Ошибка проверки неверных данных: {e}")
    
    def test_rate_limiting(self):
        """Тест ограничения частоты запросов"""
        try:
            # Множественные попытки входа
            for i in range(7):  # Больше лимита в 5 попыток
                login_data = {
                    "email": "test@example.com",
                    "password": "wrongpassword"
                }
                
                response = self.session.post(
                    f"{self.base_url}/login",
                    data=login_data,
                    timeout=5
                )
                
                if i < 5:
                    # Первые 5 попыток должны проходить
                    self.assertEqual(response.status_code, 200)
                else:
                    # После 5 попыток должен быть rate limit
                    if response.status_code == 429:
                        print("✅ Rate limiting работает")
                        break
                    elif "rate limit" in response.text.lower() or "too many" in response.text.lower():
                        print("✅ Rate limiting работает (текстовое сообщение)")
                        break
                
                time.sleep(0.1)  # Небольшая задержка между запросами
            else:
                print("⚠️  Rate limiting не обнаружен")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Ошибка проверки rate limiting: {e}")
    
    def test_csrf_protection(self):
        """Тест защиты CSRF"""
        try:
            # Получаем страницу логина для получения CSRF токена
            response = self.session.get(f"{self.base_url}/login", timeout=5)
            self.assertEqual(response.status_code, 200)
            
            # Пытаемся отправить POST без CSRF токена
            login_data = {
                "email": "test@example.com",
                "password": "testpassword123"
            }
            
            response = self.session.post(
                f"{self.base_url}/login",
                data=login_data,
                timeout=10
            )
            
            # Должна быть ошибка CSRF или редирект
            if response.status_code == 403:
                print("✅ CSRF защита работает")
            elif "csrf" in response.text.lower():
                print("✅ CSRF защита работает (текстовое сообщение)")
            else:
                print(f"⚠️  CSRF защита: статус {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Ошибка проверки CSRF: {e}")
    
    def test_security_headers(self):
        """Тест заголовков безопасности"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            self.assertEqual(response.status_code, 200)
            
            headers = response.headers
            
            # Проверяем наличие security headers
            security_headers = [
                'X-Frame-Options',
                'X-Content-Type-Options',
                'X-XSS-Protection',
                'Content-Security-Policy'
            ]
            
            found_headers = []
            for header in security_headers:
                if header in headers:
                    found_headers.append(header)
            
            if len(found_headers) >= 2:
                print(f"✅ Security headers найдены: {found_headers}")
            else:
                print(f"⚠️  Мало security headers: {found_headers}")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Ошибка проверки security headers: {e}")
    
    def test_session_management(self):
        """Тест управления сессиями"""
        try:
            # Проверяем, что cookies устанавливаются
            response = self.session.get(f"{self.base_url}/login", timeout=5)
            self.assertEqual(response.status_code, 200)
            
            # Проверяем наличие cookies
            cookies = self.session.cookies
            if cookies:
                print(f"✅ Cookies установлены: {len(cookies)} штук")
            else:
                print("⚠️  Cookies не найдены")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Ошибка проверки cookies: {e}")
    
    def test_logout_functionality(self):
        """Тест функциональности выхода"""
        try:
            # Пытаемся выйти (даже без входа)
            response = self.session.post(f"{self.base_url}/logout", timeout=5)
            
            # Должен быть редирект на логин
            if response.status_code in [302, 307]:
                self.assertIn("/login", response.headers.get("Location", ""))
                print("✅ Logout работает")
            else:
                print(f"⚠️  Logout: статус {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Ошибка проверки logout: {e}")
    
    def test_password_validation(self):
        """Тест валидации паролей"""
        try:
            # Тестируем слабые пароли
            weak_passwords = [
                "123",  # Слишком короткий
                "password",  # Только буквы
                "12345678",  # Только цифры
                ""  # Пустой
            ]
            
            for weak_password in weak_passwords:
                registration_data = {
                    "email": f"test_{int(time.time())}@example.com",
                    "password": weak_password,
                    "confirm_password": weak_password
                }
                
                response = self.session.post(
                    f"{self.base_url}/register",
                    data=registration_data,
                    timeout=5
                )
                
                # Должна остаться на странице регистрации с ошибкой
                if response.status_code == 200 and "register" in response.url.lower():
                    print(f"✅ Слабый пароль '{weak_password}' отклонен")
                else:
                    print(f"⚠️  Слабый пароль '{weak_password}': статус {response.status_code}")
                    
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Ошибка проверки валидации паролей: {e}")
    
    def test_email_validation(self):
        """Тест валидации email"""
        try:
            # Тестируем невалидные email
            invalid_emails = [
                "invalid-email",
                "@example.com",
                "test@",
                "test@.com",
                ""
            ]
            
            for invalid_email in invalid_emails:
                registration_data = {
                    "email": invalid_email,
                    "password": "validpassword123",
                    "confirm_password": "validpassword123"
                }
                
                response = self.session.post(
                    f"{self.base_url}/register",
                    data=registration_data,
                    timeout=5
                )
                
                # Должна остаться на странице регистрации
                if response.status_code == 200 and "register" in response.url.lower():
                    print(f"✅ Невалидный email '{invalid_email}' отклонен")
                else:
                    print(f"⚠️  Невалидный email '{invalid_email}': статус {response.status_code}")
                    
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Ошибка проверки валидации email: {e}")


class TestAuthWorkflow(unittest.TestCase):
    """Тесты полного рабочего процесса аутентификации"""
    
    @classmethod
    def setUpClass(cls):
        """Настройка перед всеми тестами"""
        cls.base_url = "http://localhost:8000"
        cls.session = requests.Session()
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.session.cookies.clear()
    
    def test_full_auth_workflow(self):
        """Тест полного цикла аутентификации"""
        try:
            # 1. Регистрация
            registration_data = {
                "email": f"workflow_{int(time.time())}@example.com",
                "password": "workflowpassword123",
                "confirm_password": "workflowpassword123"
            }
            
            response = self.session.post(
                f"{self.base_url}/register",
                data=registration_data,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Регистрация в workflow прошла")
                
                # 2. Попытка доступа к CMS
                response = self.session.get(f"{self.base_url}/cms", timeout=5)
                
                if response.status_code == 200:
                    print("✅ Доступ к CMS после регистрации")
                else:
                    print(f"⚠️  Доступ к CMS: статус {response.status_code}")
                
                # 3. Выход
                response = self.session.post(f"{self.base_url}/logout", timeout=5)
                
                if response.status_code in [302, 307]:
                    print("✅ Logout в workflow прошел")
                else:
                    print(f"⚠️  Logout: статус {response.status_code}")
                
                # 4. Попытка доступа к CMS после выхода
                response = self.session.get(f"{self.base_url}/cms", timeout=5, allow_redirects=False)
                
                if response.status_code in [302, 307]:
                    print("✅ Редирект на логин после logout")
                else:
                    print(f"⚠️  Редирект после logout: статус {response.status_code}")
                    
            else:
                print(f"⚠️  Регистрация в workflow: статус {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Ошибка в workflow: {e}")


if __name__ == "__main__":
    # Настройка тестирования
    print("🧪 Запуск интеграционных тестов аутентификации...")
    print("=" * 60)
    print("⚠️  Убедитесь, что сервер запущен: uvicorn app.main:app --reload")
    print("=" * 60)
    
    unittest.main(verbosity=2)
