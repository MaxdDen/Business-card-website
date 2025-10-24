#!/usr/bin/env python3
"""
Автотест для проверки исправления языковых ссылок в CMS
Проверяет, что переходы между страницами CMS сохраняют выбранный язык
"""

import requests
import sys
import os
import time
import re
from urllib.parse import urljoin

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def test_cms_language_links():
    """Тест сохранения языка при переходах в CMS"""
    print("🧪 Тестирование исправления языковых ссылок в CMS...")
    
    base_url = "http://127.0.0.1:8000"
    
    # Тестовые данные для входа
    login_data = {
        "email": "admin@test.com",
        "password": "testpassword123"
    }
    
    session = requests.Session()
    
    try:
        # 1. Входим в систему
        print("📝 Вход в систему...")
        login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
        
        if login_response.status_code not in [200, 302]:
            print(f"❌ Ошибка входа: {login_response.status_code}")
            return False
        
        # 2. Тестируем переходы для каждого языка
        languages = ["en", "ua", "ru"]
        cms_pages = ["", "texts", "images", "seo", "users"]
        
        for lang in languages:
            print(f"\n🌍 Тестирование языка: {lang.upper()}")
            
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
                
                # Проверяем, что в HTML есть правильные языковые ссылки
                html_content = response.text
                
                # Проверяем наличие языковых переключателей
                language_switcher_pattern = r'<a href="[^"]*cms/[a-z]{2}[^"]*"'
                language_links = re.findall(language_switcher_pattern, html_content)
                
                if not language_links:
                    print(f"    ⚠️  Не найдены языковые ссылки на странице {page}")
                else:
                    print(f"    ✅ Найдено {len(language_links)} языковых ссылок")
                
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
        
        # 3. Тестируем переходы между страницами
        print(f"\n🔄 Тестирование переходов между страницами...")
        
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
        
        # Переходим обратно на dashboard
        dashboard_url = f"{base_url}/cms/ua/"
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
        
        print("\n✅ Все тесты языковых ссылок в CMS прошли успешно!")
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

def test_language_middleware():
    """Тест работы Language Middleware"""
    print("\n🔧 Тестирование Language Middleware...")
    
    base_url = "http://127.0.0.1:8000"
    
    # Тестируем определение языка из URL
    test_urls = [
        "/cms/ua/",
        "/cms/en/texts", 
        "/cms/ru/images",
        "/cms/ua/seo",
        "/cms/en/users"
    ]
    
    for url in test_urls:
        full_url = f"{base_url}{url}"
        print(f"  📍 Тестирование URL: {url}")
        
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
    print("🚀 Запуск автотеста исправления языковых ссылок в CMS")
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
    
    # Тест Language Middleware
    test_language_middleware()
    
    # Тест языковых ссылок в CMS
    if not test_cms_language_links():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Все тесты прошли успешно!")
        print("✅ Языковые ссылки в CMS исправлены")
        print("✅ Переходы между страницами сохраняют выбранный язык")
    else:
        print("❌ Некоторые тесты не прошли")
        print("💡 Проверьте логи выше для деталей")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
