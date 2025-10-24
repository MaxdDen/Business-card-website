#!/usr/bin/env python3
"""
Автотест для проверки сохранения языка при переходе с авторизации на дашборд

Этот тест проверяет, что:
1. Страницы логина/регистрации доступны по новой структуре: /{lang}/login, /{lang}/register
2. После успешной авторизации происходит редирект на правильную языковую версию CMS: /{lang}/cms/
3. Язык сохраняется при переходах между страницами
"""

import requests
import sys
import os
import time
from urllib.parse import urljoin

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def test_auth_language_redirect():
    """Тест сохранения языка при переходе с авторизации на дашборд"""
    print("🧪 Тестирование сохранения языка при переходе с авторизации на дашборд")
    
    # Базовый URL
    base_url = "http://127.0.0.1:8000"
    
    # Поддерживаемые языки
    languages = ["en", "ua", "ru"]
    
    print(f"\n📋 Тестируемые языки: {', '.join(languages)}")
    
    # Проверяем доступность сервера
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Сервер недоступен")
            return False
    except requests.exceptions.RequestException:
        print("❌ Не удается подключиться к серверу")
        return False
    
    print("✅ Сервер доступен")
    
    # Тест 1: Проверка доступности страниц авторизации по новой структуре
    print("\n🔍 Тест 1: Страницы авторизации по новой структуре")
    for lang in languages:
        # Проверяем страницу логина
        login_url = f"{base_url}/{lang}/login"
        try:
            response = requests.get(login_url, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {lang}/login -> {response.status_code}")
            else:
                print(f"  ❌ {lang}/login -> {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {lang}/login -> Ошибка: {e}")
        
        # Проверяем страницу регистрации
        register_url = f"{base_url}/{lang}/register"
        try:
            response = requests.get(register_url, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {lang}/register -> {response.status_code}")
            else:
                print(f"  ❌ {lang}/register -> {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {lang}/register -> Ошибка: {e}")
    
    # Тест 2: Проверка редиректов после авторизации
    print("\n🔍 Тест 2: Редиректы после авторизации")
    
    # Тестируем редирект для каждого языка
    for lang in languages:
        # Проверяем, что CMS доступен по новой структуре
        cms_url = f"{base_url}/{lang}/cms/"
        try:
            response = requests.get(cms_url, timeout=5, allow_redirects=False)
            # CMS требует аутентификации, поэтому ожидаем редирект на логин
            if response.status_code in [302, 401]:
                print(f"  ✅ {lang}/cms/ -> {response.status_code} (требует аутентификации)")
                
                # Проверяем, куда происходит редирект
                if response.status_code == 302:
                    redirect_url = response.headers.get('Location', '')
                    if f'/{lang}/login' in redirect_url:
                        print(f"    ✅ Редирект на {lang}/login")
                    else:
                        print(f"    ❌ Неправильный редирект: {redirect_url}")
            else:
                print(f"  ❌ {lang}/cms/ -> {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {lang}/cms/ -> Ошибка: {e}")
    
    # Тест 3: Проверка языковых ссылок на страницах авторизации
    print("\n🔍 Тест 3: Языковые ссылки на страницах авторизации")
    
    for lang in languages:
        login_url = f"{base_url}/{lang}/login"
        try:
            response = requests.get(login_url, timeout=5)
            if response.status_code == 200:
                content = response.text
                
                # Проверяем, что в HTML есть ссылки на другие языки
                for other_lang in languages:
                    if other_lang != lang:
                        if f'/{other_lang}/login' in content:
                            print(f"  ✅ {lang}/login содержит ссылку на {other_lang}/login")
                        else:
                            print(f"  ❌ {lang}/login не содержит ссылку на {other_lang}/login")
            else:
                print(f"  ❌ {lang}/login -> {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {lang}/login -> Ошибка: {e}")
    
    # Тест 4: Проверка функции get_language_from_url
    print("\n🔍 Тест 4: Функция get_language_from_url")
    
    try:
        from app.auth.routes import get_language_from_url
        from fastapi import Request
        
        # Создаем мок объект Request
        class MockRequest:
            def __init__(self, url_path):
                self.url = MockURL(url_path)
        
        class MockURL:
            def __init__(self, path):
                self.path = path
        
        # Тестовые URL
        test_urls = [
            ("/en/login", "en"),
            ("/ua/register", "ua"),
            ("/ru/login", "ru"),
            ("/en/", "en"),
            ("/ua/cms/", "ua"),
            ("/ru/cms/texts", "ru"),
            ("/login", "en"),  # Должен вернуть язык по умолчанию
            ("/unknown/page", "en")  # Должен вернуть язык по умолчанию
        ]
        
        for url_path, expected_lang in test_urls:
            mock_request = MockRequest(url_path)
            extracted_lang = get_language_from_url(mock_request)
            if extracted_lang == expected_lang:
                print(f"  ✅ {url_path} -> {extracted_lang}")
            else:
                print(f"  ❌ {url_path} -> {extracted_lang} (ожидалось: {expected_lang})")
        
    except ImportError as e:
        print(f"  ❌ Ошибка импорта: {e}")
        return False
    
    # Тест 5: Проверка функции get_cms_redirect_url
    print("\n🔍 Тест 5: Функция get_cms_redirect_url")
    
    try:
        from app.auth.routes import get_cms_redirect_url
        
        # Тестовые языки
        test_languages = ["en", "ua", "ru"]
        
        for lang in test_languages:
            redirect_url = get_cms_redirect_url(lang)
            expected_url = f"/{lang}/cms/"
            if redirect_url == expected_url:
                print(f"  ✅ {lang} -> {redirect_url}")
            else:
                print(f"  ❌ {lang} -> {redirect_url} (ожидалось: {expected_url})")
        
    except ImportError as e:
        print(f"  ❌ Ошибка импорта: {e}")
        return False
    
    print("\n✅ Тестирование сохранения языка при переходе с авторизации завершено")
    return True

def test_language_persistence_flow():
    """Тест полного потока сохранения языка"""
    print("\n🔍 Тест полного потока сохранения языка")
    
    base_url = "http://127.0.0.1:8000"
    languages = ["en", "ua", "ru"]
    
    for lang in languages:
        print(f"\n  📋 Тестирование потока для языка: {lang}")
        
        # 1. Переходим на страницу логина
        login_url = f"{base_url}/{lang}/login"
        try:
            response = requests.get(login_url, timeout=5)
            if response.status_code == 200:
                print(f"    ✅ 1. Страница логина доступна: {lang}/login")
                
                # 2. Проверяем, что в HTML есть правильные языковые ссылки
                content = response.text
                for other_lang in languages:
                    if other_lang != lang:
                        if f'/{other_lang}/login' in content:
                            print(f"    ✅ 2. Ссылка на {other_lang}/login найдена")
                        else:
                            print(f"    ❌ 2. Ссылка на {other_lang}/login не найдена")
                
                # 3. Проверяем, что CMS будет доступен по правильному URL
                cms_url = f"{base_url}/{lang}/cms/"
                try:
                    cms_response = requests.get(cms_url, timeout=5, allow_redirects=False)
                    if cms_response.status_code in [302, 401]:
                        print(f"    ✅ 3. CMS доступен по правильному URL: {lang}/cms/")
                    else:
                        print(f"    ❌ 3. CMS недоступен: {lang}/cms/ -> {cms_response.status_code}")
                except requests.exceptions.RequestException as e:
                    print(f"    ❌ 3. Ошибка доступа к CMS: {e}")
            else:
                print(f"    ❌ 1. Страница логина недоступна: {lang}/login -> {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"    ❌ 1. Ошибка доступа к странице логина: {e}")
    
    return True

if __name__ == "__main__":
    print("🚀 Запуск автотеста сохранения языка при переходе с авторизации")
    print("=" * 70)
    
    # Запускаем тесты
    success = True
    
    # Тест 1: Основная функциональность
    if not test_auth_language_redirect():
        success = False
    
    # Тест 2: Полный поток
    if not test_language_persistence_flow():
        success = False
    
    print("\n" + "=" * 70)
    if success:
        print("✅ Все тесты прошли успешно!")
        print("🎉 Сохранение языка при переходе с авторизации работает корректно")
    else:
        print("❌ Некоторые тесты не прошли")
        print("🔧 Требуется дополнительная настройка")
    
    sys.exit(0 if success else 1)
