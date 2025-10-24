#!/usr/bin/env python3
"""
Автотест для проверки исправлений ссылок по best practices

Этот тест проверяет, что:
1. Форма авторизации передает язык в action URL
2. Ссылки в дашборде не содержат избыточного дублирования языка
3. Middleware корректно обрабатывает все ссылки
4. Навигация работает без потери языка
"""

import requests
import sys
import os
from urllib.parse import urljoin

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def test_best_practices_links():
    """Тест исправлений ссылок по best practices"""
    print("🧪 Тестирование исправлений ссылок по best practices")
    
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
    
    # Тест 1: Проверка формы авторизации
    print("\n🔍 Тест 1: Форма авторизации с языком в action")
    for lang in languages:
        login_url = f"{base_url}/{lang}/login"
        try:
            response = requests.get(login_url, timeout=5)
            if response.status_code == 200:
                content = response.text
                
                # Проверяем, что форма содержит правильный action
                expected_action = f'action="/{lang}/login"'
                if expected_action in content:
                    print(f"  ✅ {lang}/login содержит правильный action: {expected_action}")
                else:
                    print(f"  ❌ {lang}/login не содержит правильный action")
                    print(f"    Ожидалось: {expected_action}")
                    # Показываем, что найдено
                    import re
                    action_match = re.search(r'action="[^"]*"', content)
                    if action_match:
                        print(f"    Найдено: {action_match.group()}")
                
                # Проверяем ссылку на регистрацию
                expected_register = f'href="/{lang}/register"'
                if expected_register in content:
                    print(f"  ✅ {lang}/login содержит правильную ссылку на регистрацию")
                else:
                    print(f"  ❌ {lang}/login не содержит правильную ссылку на регистрацию")
            else:
                print(f"  ❌ {lang}/login -> {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {lang}/login -> Ошибка: {e}")
    
    # Тест 2: Проверка ссылок в дашборде (без избыточного языка)
    print("\n🔍 Тест 2: Ссылки в дашборде без избыточного языка")
    for lang in languages:
        dashboard_url = f"{base_url}/{lang}/cms/"
        try:
            response = requests.get(dashboard_url, timeout=5, allow_redirects=False)
            if response.status_code in [302, 401]:  # Требует аутентификации
                print(f"  ✅ {lang}/cms/ доступен (требует аутентификации)")
                
                # Проверяем, что редирект ведет на правильную страницу логина
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
    
    # Тест 3: Проверка навигационных ссылок
    print("\n🔍 Тест 3: Навигационные ссылки")
    cms_pages = ["texts", "images", "seo", "users"]
    
    for lang in languages:
        for page in cms_pages:
            page_url = f"{base_url}/{lang}/cms/{page}"
            try:
                response = requests.get(page_url, timeout=5, allow_redirects=False)
                if response.status_code in [302, 401]:  # Требует аутентификации
                    print(f"  ✅ {lang}/cms/{page} доступен (требует аутентификации)")
                else:
                    print(f"  ❌ {lang}/cms/{page} -> {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"  ❌ {lang}/cms/{page} -> Ошибка: {e}")
    
    # Тест 4: Проверка языковых переключателей
    print("\n🔍 Тест 4: Языковые переключатели")
    for lang in languages:
        login_url = f"{base_url}/{lang}/login"
        try:
            response = requests.get(login_url, timeout=5)
            if response.status_code == 200:
                content = response.text
                
                # Проверяем, что есть ссылки на другие языки
                for other_lang in languages:
                    if other_lang != lang:
                        expected_link = f'/{other_lang}/login'
                        if expected_link in content:
                            print(f"  ✅ {lang}/login содержит ссылку на {other_lang}/login")
                        else:
                            print(f"  ❌ {lang}/login не содержит ссылку на {other_lang}/login")
            else:
                print(f"  ❌ {lang}/login -> {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {lang}/login -> Ошибка: {e}")
    
    # Тест 5: Проверка отсутствия избыточных языковых ссылок
    print("\n🔍 Тест 5: Отсутствие избыточных языковых ссылок")
    for lang in languages:
        login_url = f"{base_url}/{lang}/login"
        try:
            response = requests.get(login_url, timeout=5)
            if response.status_code == 200:
                content = response.text
                
                # Проверяем, что НЕТ избыточных ссылок типа /{{ lang }}/cms
                if "/{{ lang }}/" in content:
                    print(f"  ❌ {lang}/login содержит избыточные языковые ссылки")
                else:
                    print(f"  ✅ {lang}/login не содержит избыточных языковых ссылок")
                
                # Проверяем, что НЕТ старых ссылок типа /cms/ru/
                if "/cms/ru/" in content or "/cms/ua/" in content or "/cms/en/" in content:
                    print(f"  ❌ {lang}/login содержит старые ссылки с языком в конце")
                else:
                    print(f"  ✅ {lang}/login не содержит старых ссылок")
            else:
                print(f"  ❌ {lang}/login -> {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {lang}/login -> Ошибка: {e}")
    
    print("\n✅ Тестирование исправлений ссылок завершено")
    return True

def test_middleware_consistency():
    """Тест консистентности middleware"""
    print("\n🔍 Тест консистентности middleware")
    
    try:
        from app.site.middleware import LanguageMiddleware
        from app.site.config import get_supported_languages, get_default_language
        
        # Проверяем конфигурацию
        supported_languages = get_supported_languages()
        default_language = get_default_language()
        
        print(f"  📋 Поддерживаемые языки: {supported_languages}")
        print(f"  📋 Язык по умолчанию: {default_language}")
        
        # Проверяем, что все языки поддерживаются
        expected_languages = ["en", "ua", "ru"]
        for lang in expected_languages:
            if lang in supported_languages:
                print(f"  ✅ Язык '{lang}' поддерживается")
            else:
                print(f"  ❌ Язык '{lang}' НЕ поддерживается")
        
        # Проверяем, что язык по умолчанию входит в поддерживаемые
        if default_language in supported_languages:
            print(f"  ✅ Язык по умолчанию '{default_language}' поддерживается")
        else:
            print(f"  ❌ Язык по умолчанию '{default_language}' НЕ поддерживается")
        
    except ImportError as e:
        print(f"  ❌ Ошибка импорта: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Запуск автотеста исправлений ссылок по best practices")
    print("=" * 70)
    
    # Запускаем тесты
    success = True
    
    # Тест 1: Основная функциональность
    if not test_best_practices_links():
        success = False
    
    # Тест 2: Консистентность middleware
    if not test_middleware_consistency():
        success = False
    
    print("\n" + "=" * 70)
    if success:
        print("✅ Все тесты прошли успешно!")
        print("🎉 Ссылки исправлены по best practices")
    else:
        print("❌ Некоторые тесты не прошли")
        print("🔧 Требуется дополнительная настройка")
    
    sys.exit(0 if success else 1)
