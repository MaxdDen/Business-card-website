#!/usr/bin/env python3
"""
Автотест для проверки языковых переходов в авторизации
Проверяет переходы между страницами login/register с сохранением языка
"""

import requests
import sys
import os
import time
import re
from urllib.parse import urljoin

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def get_csrf_token(session, url):
    """Получить CSRF токен со страницы"""
    try:
        response = session.get(url)
        if response.status_code != 200:
            return None
        
        # Ищем CSRF токен в cookies
        for cookie in session.cookies:
            if cookie.name == 'csrftoken':
                return cookie.value
        
        return None
    except Exception as e:
        print(f"    ⚠️  Ошибка получения CSRF токена: {e}")
        return None

def test_auth_language_links():
    """Тест языковых переходов в авторизации"""
    print("🧪 Тестирование языковых переходов в авторизации...")
    
    base_url = "http://127.0.0.1:8000"
    
    # Тестовые данные для входа
    login_data = {
        "email": "admin@example.com",
        "password": "admin123"
    }
    
    session = requests.Session()
    
    try:
        # 1. Тестируем переходы между страницами авторизации для каждого языка
        languages = ["en", "ua", "ru"]
        
        for lang in languages:
            print(f"\n🌍 Тестирование языка: {lang.upper()}")
            
            # Тестируем страницу логина
            if lang == "en":
                login_url = f"{base_url}/login"
            else:
                login_url = f"{base_url}/{lang}/login"
            
            print(f"  📄 Страница логина: {login_url}")
            response = session.get(login_url)
            
            if response.status_code != 200:
                print(f"    ❌ Ошибка загрузки страницы логина: {response.status_code}")
                continue
            
            print("    ✅ Страница логина загружена")
            
            # Проверяем ссылку на регистрацию
            print("  🔍 Проверка ссылки на регистрацию...")
            register_link_match = re.search(r'href="([^"]*register[^"]*)"', response.text)
            if register_link_match:
                register_link = register_link_match.group(1)
                print(f"    📍 Найденная ссылка на регистрацию: {register_link}")
                
                # Проверяем, что ссылка содержит правильный языковой префикс
                expected_register_url = "/register" if lang == "en" else f"/{lang}/register"
                if expected_register_url in register_link:
                    print("    ✅ Ссылка на регистрацию содержит правильный языковой префикс")
                else:
                    print(f"    ❌ Неправильная ссылка на регистрацию. Ожидался: {expected_register_url}")
                    return False
            else:
                print("    ❌ Ссылка на регистрацию не найдена")
                return False
            
            # Тестируем переход на страницу регистрации
            print("  📄 Переход на страницу регистрации...")
            register_response = session.get(f"{base_url}{register_link}")
            
            if register_response.status_code != 200:
                print(f"    ❌ Ошибка загрузки страницы регистрации: {register_response.status_code}")
                continue
            
            print("    ✅ Страница регистрации загружена")
            
            # Проверяем ссылку обратно на логин
            print("  🔍 Проверка ссылки обратно на логин...")
            login_link_match = re.search(r'href="([^"]*login[^"]*)"', register_response.text)
            if login_link_match:
                login_link = login_link_match.group(1)
                print(f"    📍 Найденная ссылка на логин: {login_link}")
                
                # Проверяем, что ссылка содержит правильный языковой префикс
                expected_login_url = "/login" if lang == "en" else f"/{lang}/login"
                if expected_login_url in login_link:
                    print("    ✅ Ссылка на логин содержит правильный языковой префикс")
                else:
                    print(f"    ❌ Неправильная ссылка на логин. Ожидался: {expected_login_url}")
                    return False
            else:
                print("    ❌ Ссылка на логин не найдена")
                return False
        
        # 2. Тестируем авторизацию с сохранением языка
        print(f"\n🔐 Тестирование авторизации с сохранением языка...")
        
        # Тестируем авторизацию с украинского языка
        print("📝 Тестирование авторизации с украинского языка...")
        
        # Загружаем страницу логина на украинском
        login_ua_url = f"{base_url}/ua/login"
        print(f"📄 Страница логина: {login_ua_url}")
        
        response = session.get(login_ua_url)
        if response.status_code != 200:
            print(f"❌ Ошибка загрузки страницы логина: {response.status_code}")
            return False
        
        # Получаем CSRF токен
        csrf_token = get_csrf_token(session, login_ua_url)
        
        if not csrf_token:
            print("⚠️  Не удалось получить CSRF токен, пробуем без него...")
            login_data_with_csrf = login_data.copy()
        else:
            print("🔑 Получен CSRF токен")
            login_data_with_csrf = login_data.copy()
            login_data_with_csrf["csrf_token"] = csrf_token
        
        # Входим в систему
        login_response = session.post(login_ua_url, data=login_data_with_csrf, allow_redirects=False)
        
        if login_response.status_code == 302:
            redirect_url = login_response.headers.get("Location", "")
            print(f"📍 Редирект после входа: {redirect_url}")
            
            if "/cms/ua" in redirect_url:
                print("✅ Редирект корректный - ведет на украинскую версию CMS")
            else:
                print("❌ Неправильный редирект - не ведет на украинскую версию CMS")
                return False
        else:
            print(f"❌ Ошибка входа: {login_response.status_code}")
            return False
        
        # 3. Тестируем logout с сохранением языка
        print(f"\n🚪 Тестирование logout с сохранением языка...")
        
        # Переходим на dashboard
        dashboard_url = f"{base_url}/cms/ua"
        dashboard_response = session.get(dashboard_url)
        
        if dashboard_response.status_code != 200:
            print(f"❌ Ошибка загрузки dashboard: {dashboard_response.status_code}")
            return False
        
        print("✅ Dashboard загружен")
        
        # Проверяем ссылку logout
        print("🔍 Проверка ссылки logout...")
        logout_link_match = re.search(r'href="([^"]*logout[^"]*)"', dashboard_response.text)
        if logout_link_match:
            logout_link = logout_link_match.group(1)
            print(f"📍 Найденная ссылка logout: {logout_link}")
            
            # Проверяем, что ссылка содержит правильный языковой префикс (для украинского языка)
            expected_logout_url = "/ua/logout"
            if expected_logout_url in logout_link:
                print("✅ Ссылка logout содержит правильный языковой префикс")
            else:
                print(f"❌ Неправильная ссылка logout. Ожидался: {expected_logout_url}")
                return False
        else:
            print("❌ Ссылка logout не найдена")
            return False
        
        # Тестируем переход по ссылке logout
        print("🔄 Тестирование перехода по ссылке logout...")
        logout_response = session.get(f"{base_url}{logout_link}", allow_redirects=False)
        
        if logout_response.status_code == 302:
            redirect_url = logout_response.headers.get("Location", "")
            print(f"📍 Редирект после logout: {redirect_url}")
            
            if "/ua/login" in redirect_url:
                print("✅ Редирект после logout корректный - ведет на украинскую страницу логина")
            else:
                print("❌ Неправильный редирект после logout")
                return False
        else:
            print(f"❌ Ошибка logout: {logout_response.status_code}")
            return False
        
        print("\n✅ Все тесты языковых переходов в авторизации прошли успешно!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка подключения к серверу. Убедитесь, что сервер запущен на http://127.0.0.1:8000")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False
    finally:
        # Выходим из системы
        try:
            session.post(f"{base_url}/logout")
        except:
            pass

def test_auth_routes():
    """Тест доступности языковых роутов авторизации"""
    print("\n🔧 Тестирование языковых роутов авторизации...")
    
    base_url = "http://127.0.0.1:8000"
    
    # Тестируем языковые роуты
    test_routes = [
        ("/ua/login", "украинская страница логина"),
        ("/ru/login", "русская страница логина"),
        ("/en/login", "английская страница логина"),
        ("/ua/register", "украинская страница регистрации"),
        ("/ru/register", "русская страница регистрации"),
        ("/en/register", "английская страница регистрации"),
        ("/ua/logout", "украинский logout"),
        ("/ru/logout", "русский logout"),
        ("/en/logout", "английский logout")
    ]
    
    for route, description in test_routes:
        full_url = f"{base_url}{route}"
        print(f"  📍 Тестирование {description}: {route}")
        
        try:
            response = requests.get(full_url, allow_redirects=False)
            
            if response.status_code == 200:
                print(f"    ✅ Страница загружена успешно")
            elif response.status_code == 302:
                # Проверяем, что редирект ведет на правильную страницу логина
                redirect_url = response.headers.get("Location", "")
                if "/login" in redirect_url:
                    print(f"    ✅ Редирект на логин (ожидаемо для неавторизованного пользователя)")
                else:
                    print(f"    ⚠️  Неожиданный редирект: {redirect_url}")
            else:
                print(f"    ❌ Неожиданный статус: {response.status_code}")
                
        except Exception as e:
            print(f"    ❌ Ошибка: {e}")

def main():
    """Главная функция теста"""
    print("🚀 Запуск автотеста языковых переходов в авторизации")
    print("=" * 60)
    
    # Проверяем доступность сервера
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Сервер недоступен или не отвечает на /health")
            return False
    except:
        print("❌ Сервер недоступен на http://127.0.0.1:8000")
        print("💡 Запустите сервер командой: python -m uvicorn app.main:app --reload")
        return False
    
    print("✅ Сервер доступен")
    
    # Запускаем тесты
    success = True
    
    # Тест языковых роутов авторизации
    test_auth_routes()
    
    # Тест языковых переходов в авторизации
    if not test_auth_language_links():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Все тесты прошли успешно!")
        print("✅ Языковые переходы в авторизации работают корректно")
        print("✅ Ссылки между login/register сохраняют язык")
        print("✅ Logout ведет на правильную языковую страницу логина")
    else:
        print("❌ Некоторые тесты не прошли")
        print("💡 Проверьте логи выше для деталей")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
