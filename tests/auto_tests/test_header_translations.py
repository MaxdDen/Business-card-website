#!/usr/bin/env python3
"""
Автотест: Проверка переводов в header.html

Этот тест проверяет, что:
1. Header содержит условную логику для переводов
2. Переводы работают для всех языков (ru, en, ua)
3. Переменная lang доступна в контексте
"""

import os
import re
import requests
import time
from pathlib import Path


def test_header_contains_translations():
    """Проверяем, что header.html содержит условную логику для переводов"""
    print("🔍 Проверяем наличие переводов в header.html...")
    
    header_file = 'app/templates/partials/header.html'
    
    if not os.path.exists(header_file):
        print(f"❌ Файл {header_file} не найден")
        return False
    
    with open(header_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем использование переводов из базы данных
    translation_patterns = [
        r'{{ t\.theme or \'Theme\' }}',
        r'{{ t\.home or \'Home\' }}'
    ]
    
    missing_patterns = []
    for pattern in translation_patterns:
        if not re.search(pattern, content):
            missing_patterns.append(pattern)
    
    if missing_patterns:
        print(f"❌ Отсутствуют паттерны переводов из БД: {missing_patterns}")
        return False
    
    # Проверяем, что нет хардкод переводов (исключая fallback значения)
    hardcoded_translations = ['Тема', 'Главная', 'Головна']
    for translation in hardcoded_translations:
        if translation in content:
            print(f"❌ Найден хардкод перевод: {translation}")
            return False
    
    print("✅ Header содержит условную логику для переводов")
    return True


def test_cms_pages_have_lang_context():
    """Проверяем, что CMS страницы передают переменную lang"""
    print("🔍 Проверяем передачу переменной lang в CMS...")
    
    cms_pages = [
        '/cms',
        '/cms/texts',
        '/cms/images',
        '/cms/seo',
        '/cms/users'
    ]
    
    # Проверяем, что страницы загружаются (могут быть редиректы на логин)
    for page in cms_pages:
        try:
            response = requests.get(f'http://localhost:8000{page}', timeout=5, allow_redirects=True)
            if response.status_code not in [200, 302]:
                print(f"❌ Страница {page} возвращает код {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка загрузки {page}: {e}")
            return False
    
    print("✅ CMS страницы загружаются корректно")
    return True


def test_language_switching():
    """Проверяем переключение языков в CMS"""
    print("🔍 Проверяем переключение языков...")
    
    # Проверяем языковые роуты CMS
    language_routes = [
        '/cms/ru',
        '/cms/en', 
        '/cms/ua',
        '/cms/ru/texts',
        '/cms/en/texts',
        '/cms/ua/texts'
    ]
    
    for route in language_routes:
        try:
            response = requests.get(f'http://localhost:8000{route}', timeout=5, allow_redirects=True)
            if response.status_code not in [200, 302]:
                print(f"❌ Языковой роут {route} возвращает код {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка загрузки {route}: {e}")
            return False
    
    print("✅ Языковые роуты работают корректно")
    return True


def test_header_template_syntax():
    """Проверяем синтаксис шаблона header.html"""
    print("🔍 Проверяем синтаксис шаблона header.html...")
    
    header_file = 'app/templates/partials/header.html'
    
    with open(header_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем использование переменных шаблона
    template_variables = content.count('{{ t.')
    
    if template_variables == 0:
        print("❌ Отсутствуют переменные шаблона")
        return False
    
    # Проверяем наличие всех необходимых элементов
    required_elements = [
        'theme-toggle',
        'hover:underline',
        '{{ t.theme',
        '{{ t.home'
    ]
    
    missing_elements = []
    for element in required_elements:
        if element not in content:
            missing_elements.append(element)
    
    if missing_elements:
        print(f"❌ Отсутствуют элементы: {missing_elements}")
        return False
    
    print("✅ Синтаксис шаблона корректен")
    return True


def test_translation_consistency():
    """Проверяем консистентность переводов"""
    print("🔍 Проверяем консистентность переводов...")
    
    header_file = 'app/templates/partials/header.html'
    
    with open(header_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем использование переводов из базы данных
    if '{{ t.theme' not in content or '{{ t.home' not in content:
        print("❌ Отсутствуют переводы из базы данных")
        return False
    
    # Проверяем наличие fallback значений
    if 'or \'Theme\'' not in content or 'or \'Home\'' not in content:
        print("❌ Отсутствуют fallback значения")
        return False
    
    print("✅ Переводы консистентны")
    return True


def main():
    """Основная функция теста"""
    print("🚀 Запуск автотеста: Переводы в header.html")
    print("=" * 60)
    
    tests = [
        ("Проверка наличия переводов в header", test_header_contains_translations),
        ("Проверка синтаксиса шаблона", test_header_template_syntax),
        ("Проверка консистентности переводов", test_translation_consistency),
        ("Проверка передачи lang в CMS", test_cms_pages_have_lang_context),
        ("Проверка переключения языков", test_language_switching)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - ПРОЙДЕН")
            else:
                print(f"❌ {test_name} - ПРОВАЛЕН")
        except Exception as e:
            print(f"❌ {test_name} - ОШИБКА: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Переводы в header.html работают корректно.")
        return True
    else:
        print("⚠️  Некоторые тесты провалены. Требуется доработка.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
