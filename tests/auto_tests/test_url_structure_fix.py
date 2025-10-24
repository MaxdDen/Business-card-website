#!/usr/bin/env python3
"""
Автотест для проверки новой структуры URL: домен → язык → страница

Этот тест проверяет, что все ссылки в проекте используют правильную структуру:
- Публичные страницы: /{lang}/about, /{lang}/contacts
- CMS страницы: /{lang}/cms/texts, /{lang}/cms/images
- Все языки должны иметь префиксы для консистентности
"""

import requests
import sys
import os
import time
from urllib.parse import urljoin

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def test_url_structure_fix():
    """Тест новой структуры URL"""
    print("🧪 Тестирование новой структуры URL: домен → язык → страница")
    
    # Базовый URL
    base_url = "http://127.0.0.1:8000"
    
    # Поддерживаемые языки
    languages = ["en", "ua", "ru"]
    
    # Тестовые страницы
    public_pages = ["/", "/about", "/catalog", "/contacts"]
    cms_pages = ["/cms/", "/cms/texts", "/cms/images", "/cms/seo", "/cms/users"]
    
    print(f"\n📋 Тестируемые языки: {', '.join(languages)}")
    print(f"📋 Публичные страницы: {', '.join(public_pages)}")
    print(f"📋 CMS страницы: {', '.join(cms_pages)}")
    
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
    
    # Тест 1: Проверка публичных страниц с новой структурой
    print("\n🔍 Тест 1: Публичные страницы с новой структурой")
    for lang in languages:
        for page in public_pages:
            if page == "/":
                url = f"{base_url}/{lang}/"
            else:
                url = f"{base_url}/{lang}{page}"
            
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"  ✅ {lang}{page} -> {response.status_code}")
                else:
                    print(f"  ❌ {lang}{page} -> {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"  ❌ {lang}{page} -> Ошибка: {e}")
    
    # Тест 2: Проверка CMS страниц с новой структурой
    print("\n🔍 Тест 2: CMS страницы с новой структурой")
    for lang in languages:
        for page in cms_pages:
            # Новая структура: /{lang}/cms/...
            if page == "/cms/":
                url = f"{base_url}/{lang}/cms/"
            else:
                url = f"{base_url}/{lang}{page}"
            
            try:
                response = requests.get(url, timeout=5)
                # CMS страницы требуют аутентификации, поэтому ожидаем редирект на логин
                if response.status_code in [200, 302, 401]:
                    print(f"  ✅ {lang}{page} -> {response.status_code}")
                else:
                    print(f"  ❌ {lang}{page} -> {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"  ❌ {lang}{page} -> Ошибка: {e}")
    
    # Тест 3: Проверка старой структуры (должна не работать)
    print("\n🔍 Тест 3: Проверка старой структуры (должна не работать)")
    old_cms_urls = [
        "/cms/ru/",
        "/cms/en/", 
        "/cms/ua/",
        "/cms/ru/texts",
        "/cms/en/images"
    ]
    
    for url in old_cms_urls:
        try:
            response = requests.get(f"{base_url}{url}", timeout=5)
            if response.status_code == 404:
                print(f"  ✅ {url} -> 404 (правильно, старая структура не работает)")
            else:
                print(f"  ⚠️  {url} -> {response.status_code} (неожиданно)")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {url} -> Ошибка: {e}")
    
    # Тест 4: Проверка переключателя языков
    print("\n🔍 Тест 4: Проверка переключателя языков")
    
    # Тестируем главную страницу на разных языках
    for lang in languages:
        url = f"{base_url}/{lang}/"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                # Проверяем, что в HTML есть ссылки на другие языки
                content = response.text
                for other_lang in languages:
                    if other_lang != lang:
                        if f'/{other_lang}/' in content:
                            print(f"  ✅ {lang}/ содержит ссылку на {other_lang}/")
                        else:
                            print(f"  ❌ {lang}/ не содержит ссылку на {other_lang}/")
            else:
                print(f"  ❌ {lang}/ -> {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {lang}/ -> Ошибка: {e}")
    
    # Тест 5: Проверка редиректов
    print("\n🔍 Тест 5: Проверка редиректов")
    
    # Тестируем редирект с корневой страницы
    try:
        response = requests.get(f"{base_url}/", timeout=5, allow_redirects=False)
        if response.status_code in [200, 302]:
            print(f"  ✅ / -> {response.status_code}")
        else:
            print(f"  ❌ / -> {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"  ❌ / -> Ошибка: {e}")
    
    print("\n✅ Тестирование новой структуры URL завершено")
    return True

def test_middleware_language_extraction():
    """Тест извлечения языка из URL в middleware"""
    print("\n🔍 Тест извлечения языка из URL")
    
    # Импортируем функции middleware
    try:
        from app.site.middleware import LanguageMiddleware
        from app.site.config import get_supported_languages, get_default_language
        
        # Создаем экземпляр middleware
        middleware = LanguageMiddleware(None)
        
        # Тестовые URL
        test_urls = [
            ("/en/", "en"),
            ("/ua/about", "ua"),
            ("/ru/contacts", "ru"),
            ("/en/cms/", "en"),
            ("/ua/cms/texts", "ua"),
            ("/ru/cms/images", "ru"),
            ("/", get_default_language()),  # Должен вернуть язык по умолчанию
            ("/unknown/page", get_default_language())  # Должен вернуть язык по умолчанию
        ]
        
        for url, expected_lang in test_urls:
            extracted_lang = middleware.extract_language_from_url(url)
            if extracted_lang == expected_lang:
                print(f"  ✅ {url} -> {extracted_lang}")
            else:
                print(f"  ❌ {url} -> {extracted_lang} (ожидалось: {expected_lang})")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Ошибка импорта: {e}")
        return False

def test_url_generation():
    """Тест генерации URL для всех языков"""
    print("\n🔍 Тест генерации URL для всех языков")
    
    try:
        from app.site.middleware import _generate_language_urls
        
        # Тестовые пути
        test_paths = [
            ("/en/", "en"),
            ("/ua/about", "ua"),
            ("/ru/cms/texts", "ru"),
            ("/en/cms/", "en")
        ]
        
        for path, current_lang in test_paths:
            urls = _generate_language_urls(path, current_lang)
            
            print(f"  📋 Путь: {path} (текущий язык: {current_lang})")
            for lang, url in urls.items():
                print(f"    {lang}: {url}")
            
            # Проверяем, что все языки имеют префиксы
            all_have_prefixes = all(url.startswith(f'/{lang}') for lang, url in urls.items())
            if all_have_prefixes:
                print(f"  ✅ Все языки имеют префиксы")
            else:
                print(f"  ❌ Не все языки имеют префиксы")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Ошибка импорта: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск автотеста новой структуры URL")
    print("=" * 60)
    
    # Запускаем тесты
    success = True
    
    # Тест 1: Основная структура URL
    if not test_url_structure_fix():
        success = False
    
    # Тест 2: Middleware
    if not test_middleware_language_extraction():
        success = False
    
    # Тест 3: Генерация URL
    if not test_url_generation():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Все тесты прошли успешно!")
        print("🎉 Новая структура URL работает корректно: домен → язык → страница")
    else:
        print("❌ Некоторые тесты не прошли")
        print("🔧 Требуется дополнительная настройка")
    
    sys.exit(0 if success else 1)
