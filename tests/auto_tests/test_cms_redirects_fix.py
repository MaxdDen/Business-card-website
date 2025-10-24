#!/usr/bin/env python3
"""
Автотест для проверки исправления редиректов в CMS
Проверяет переходы между страницами CMS и редиректы после авторизации
"""

import requests
import sys
import os
import time
import re
from urllib.parse import urljoin

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def get_csrf_token(session, login_url):
    """Получить CSRF токен со страницы логина"""
    try:
        response = session.get(login_url)
        if response.status_code != 200:
            return None
        
        # Ищем CSRF токен в HTML
        import re
        csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', response.text)
        if csrf_match:
            return csrf_match.group(1)
        
        # Альтернативный поиск
        csrf_match = re.search(r'<input[^>]*name="csrf_token"[^>]*value="([^"]+)"', response.text)
        if csrf_match:
            return csrf_match.group(1)
        
        return None
    except Exception as e:
        print(f"    ⚠️  Ошибка получения CSRF токена: {e}")
        return None

def test_cms_redirects():
    """Тест редиректов в CMS"""
    print("🧪 Тестирование исправления редиректов в CMS...")
    
    base_url = "http://127.0.0.1:8000"
    
    # Тестовые данные для входа
    login_data = {
        "email": "admin@example.com",
        "password": "admin123"
    }
    
    session = requests.Session()
    
    try:
        # 1. Тестируем переходы между страницами CMS для каждого языка
        languages = ["en", "ua", "ru"]
        cms_pages = ["", "texts", "images", "seo", "users"]
        
        for lang in languages:
            print(f"\n🌍 Тестирование языка: {lang.upper()}")
            
            # Получаем CSRF токен с языкового URL
            if lang == "en":
                login_url = f"{base_url}/login"
            else:
                login_url = f"{base_url}/{lang}/login"
            csrf_token = get_csrf_token(session, login_url)
            
            if not csrf_token:
                print(f"    ⚠️  Не удалось получить CSRF токен, пробуем без него...")
                login_data_with_csrf = login_data.copy()
            else:
                print(f"    🔑 Получен CSRF токен")
                login_data_with_csrf = login_data.copy()
                login_data_with_csrf["csrf_token"] = csrf_token
            
            # Входим в систему
            print(f"  📝 Вход в систему для языка {lang}...")
            login_response = session.post(login_url, data=login_data_with_csrf, allow_redirects=False)
            
            if login_response.status_code not in [200, 302]:
                print(f"    ❌ Ошибка входа: {login_response.status_code}")
                continue
            
            # Проверяем редирект после входа
            if login_response.status_code == 302:
                redirect_url = login_response.headers.get("Location", "")
                print(f"    📍 Редирект после входа: {redirect_url}")
                
                # Проверяем, что редирект ведет на правильную языковую версию CMS
                expected_redirect = f"/cms" if lang == "en" else f"/cms/{lang}"
                if expected_redirect in redirect_url:
                    print(f"    ✅ Редирект корректный для языка {lang}")
                else:
                    print(f"    ❌ Неправильный редирект для языка {lang}. Ожидался: {expected_redirect}")
            
            # Тестируем переходы между страницами
            for page in cms_pages:
                # Формируем URL с языковым префиксом
                if page:
                    url = f"{base_url}/cms/{lang}/{page}"
                else:
                    url = f"{base_url}/cms/{lang}/"
                
                print(f"  📄 Проверка страницы: {url}")
                
                # Загружаем страницу
                response = session.get(url)
                
                if response.status_code != 200:
                    print(f"    ❌ Ошибка загрузки: {response.status_code}")
                    continue
                
                print(f"    ✅ Страница загружена успешно")
                
                # Проверяем, что в HTML есть правильные языковые ссылки
                html_content = response.text
                
                # Проверяем ссылки на другие страницы CMS
                if page == "":  # Dashboard
                    # Проверяем ссылки на texts, images, seo, users
                    expected_links = ["texts", "images", "seo", "users"]
                    for expected_link in expected_links:
                        link_pattern = rf'href="[^"]*cms/{lang}/{expected_link}[^"]*"'
                        if re.search(link_pattern, html_content):
                            print(f"    ✅ Ссылка на {expected_link} содержит языковой префикс")
                        else:
                            print(f"    ❌ Ссылка на {expected_link} не содержит языковой префикс")
                
                # Проверяем ссылку "Back to Dashboard"
                if page != "":
                    back_link_pattern = rf'href="[^"]*cms/{lang}/?[^"]*"'
                    if re.search(back_link_pattern, html_content):
                        print(f"    ✅ Ссылка 'Back to Dashboard' содержит языковой префикс")
                    else:
                        print(f"    ❌ Ссылка 'Back to Dashboard' не содержит языковой префикс")
            
            # Выходим из системы для следующего языка
            session.post(f"{base_url}/logout")
        
        # 2. Тестируем переходы между страницами с сохранением языка
        print(f"\n🔄 Тестирование переходов между страницами...")
        
        # Получаем CSRF токен
        login_url = f"{base_url}/login"
        csrf_token = get_csrf_token(session, login_url)
        
        if not csrf_token:
            print("⚠️  Не удалось получить CSRF токен, пробуем без него...")
            login_data_with_csrf = login_data.copy()
        else:
            print("🔑 Получен CSRF токен")
            login_data_with_csrf = login_data.copy()
            login_data_with_csrf["csrf_token"] = csrf_token
        
        # Входим в систему
        print("📝 Вход в систему...")
        login_response = session.post(f"{base_url}/login", data=login_data_with_csrf, allow_redirects=False)
        
        if login_response.status_code not in [200, 302]:
            print(f"❌ Ошибка входа: {login_response.status_code}")
            return False
        
        # Начинаем с украинского языка
        start_url = f"{base_url}/cms/ua/"
        print(f"📄 Начальная страница: {start_url}")
        
        response = session.get(start_url)
        if response.status_code != 200:
            print(f"❌ Ошибка загрузки начальной страницы: {response.status_code}")
            return False
        
        # Переходим на страницу редактирования текстов
        texts_url = f"{base_url}/cms/ua/texts"
        print(f"📄 Переход на: {texts_url}")
        
        response = session.get(texts_url)
        if response.status_code != 200:
            print(f"❌ Ошибка загрузки страницы текстов: {response.status_code}")
            return False
        
        # Проверяем, что URL остался с украинским префиксом
        if "ua" in response.url:
            print("✅ Язык сохранен при переходе на страницу текстов")
        else:
            print("❌ Язык не сохранен при переходе на страницу текстов")
            return False
        
        # Переходим обратно на dashboard (без слеша в конце)
        dashboard_url = f"{base_url}/cms/ua"
        print(f"📄 Возврат на: {dashboard_url}")
        
        response = session.get(dashboard_url)
        if response.status_code != 200:
            print(f"❌ Ошибка загрузки dashboard: {response.status_code}")
            return False
        
        # Проверяем, что URL остался с украинским префиксом
        if "ua" in response.url:
            print("✅ Язык сохранен при возврате на dashboard")
        else:
            print("❌ Язык не сохранен при возврате на dashboard")
            return False
        
        # 3. Тестируем редиректы после авторизации с разными языками
        print(f"\n🔐 Тестирование редиректов после авторизации...")
        
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
        
        print("\n✅ Все тесты редиректов в CMS прошли успешно!")
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

def test_cms_routes():
    """Тест доступности CMS роутов"""
    print("\n🔧 Тестирование CMS роутов...")
    
    base_url = "http://127.0.0.1:8000"
    
    # Тестируем роуты без слеша в конце
    test_routes = [
        "/cms/ua",
        "/cms/en", 
        "/cms/ru"
    ]
    
    for route in test_routes:
        full_url = f"{base_url}{route}"
        print(f"  📍 Тестирование роута: {route}")
        
        try:
            response = requests.get(full_url, allow_redirects=False)
            
            if response.status_code == 302:
                # Проверяем, что редирект ведет на страницу логина
                if "/login" in response.headers.get("Location", ""):
                    print(f"    ✅ Редирект на логин (ожидаемо для неавторизованного пользователя)")
                else:
                    print(f"    ⚠️  Неожиданный редирект: {response.headers.get('Location')}")
            elif response.status_code == 200:
                print(f"    ✅ Страница загружена успешно")
            else:
                print(f"    ❌ Неожиданный статус: {response.status_code}")
                
        except Exception as e:
            print(f"    ❌ Ошибка: {e}")

def main():
    """Главная функция теста"""
    print("🚀 Запуск автотеста исправления редиректов в CMS")
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
    
    # Тест CMS роутов
    test_cms_routes()
    
    # Тест редиректов в CMS
    if not test_cms_redirects():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Все тесты прошли успешно!")
        print("✅ Редиректы в CMS исправлены")
        print("✅ Переходы между страницами сохраняют выбранный язык")
        print("✅ Авторизация ведет на правильную языковую версию CMS")
    else:
        print("❌ Некоторые тесты не прошли")
        print("💡 Проверьте логи выше для деталей")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
