#!/usr/bin/env python3
"""
Автотест: Проверка выноса скриптов из HTML в отдельные JS файлы

Этот тест проверяет, что:
1. Все скрипты вынесены из HTML файлов в отдельные JS файлы
2. HTML файлы подключают внешние JS файлы
3. JS файлы содержат корректный код
4. Функциональность работает после выноса скриптов
"""

import os
import re
import requests
import time
from pathlib import Path


def test_js_files_exist():
    """Проверяем, что все необходимые JS файлы созданы"""
    print("🔍 Проверяем наличие JS файлов...")
    
    js_files = [
        'app/static/js/theme.js',
        'app/static/js/texts.js', 
        'app/static/js/users.js',
        'app/static/js/seo.js',
        'app/static/js/images.js'
    ]
    
    missing_files = []
    for js_file in js_files:
        if not os.path.exists(js_file):
            missing_files.append(js_file)
    
    if missing_files:
        print(f"❌ Отсутствуют JS файлы: {missing_files}")
        return False
    
    print("✅ Все JS файлы созданы")
    return True


def test_html_files_no_inline_scripts():
    """Проверяем, что в HTML файлах нет встроенных скриптов"""
    print("🔍 Проверяем отсутствие встроенных скриптов в HTML...")
    
    html_files = [
        'app/templates/base.html',
        'app/templates/public/base.html',
        'app/templates/texts.html',
        'app/templates/users.html',
        'app/templates/seo.html',
        'app/templates/images.html'
    ]
    
    inline_scripts_found = []
    
    for html_file in html_files:
        if not os.path.exists(html_file):
            continue
            
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Ищем встроенные скрипты (не src=)
        script_pattern = r'<script(?![^>]*src=)[^>]*>.*?</script>'
        matches = re.findall(script_pattern, content, re.DOTALL | re.IGNORECASE)
        
        if matches:
            inline_scripts_found.append({
                'file': html_file,
                'count': len(matches),
                'scripts': matches[:2]  # Показываем первые 2 для примера
            })
    
    if inline_scripts_found:
        print("❌ Найдены встроенные скрипты в HTML файлах:")
        for item in inline_scripts_found:
            print(f"  - {item['file']}: {item['count']} скриптов")
            for script in item['scripts']:
                print(f"    {script[:100]}...")
        return False
    
    print("✅ Встроенные скрипты отсутствуют в HTML файлах")
    return True


def test_html_files_include_js():
    """Проверяем, что HTML файлы подключают внешние JS файлы"""
    print("🔍 Проверяем подключение внешних JS файлов...")
    
    expected_js_links = {
        'app/templates/base.html': 'js/theme.js',
        'app/templates/public/base.html': 'js/theme.js',
        'app/templates/texts.html': 'js/texts.js',
        'app/templates/users.html': 'js/users.js',
        'app/templates/seo.html': 'js/seo.js',
        'app/templates/images.html': 'js/images.js'
    }
    
    missing_links = []
    
    for html_file, expected_js in expected_js_links.items():
        if not os.path.exists(html_file):
            continue
            
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if expected_js not in content:
            missing_links.append(f"{html_file} -> {expected_js}")
    
    if missing_links:
        print("❌ Отсутствуют ссылки на JS файлы:")
        for link in missing_links:
            print(f"  - {link}")
        return False
    
    print("✅ Все HTML файлы подключают внешние JS файлы")
    return True


def test_js_files_content():
    """Проверяем содержимое JS файлов"""
    print("🔍 Проверяем содержимое JS файлов...")
    
    js_files = {
        'app/static/js/theme.js': ['toggleTheme', 'DOMContentLoaded'],
        'app/static/js/texts.js': ['loadTexts', 'showNotification'],
        'app/static/js/users.js': ['loadUsers', 'renderUsers', 'deleteUser'],
        'app/static/js/seo.js': ['loadSeoData', 'saveSeoData', 'updatePreview'],
        'app/static/js/images.js': ['loadImages', 'renderImages', 'deleteImage']
    }
    
    content_issues = []
    
    for js_file, expected_functions in js_files.items():
        if not os.path.exists(js_file):
            content_issues.append(f"Файл {js_file} не найден")
            continue
            
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        missing_functions = []
        for func in expected_functions:
            if func not in content:
                missing_functions.append(func)
        
        if missing_functions:
            content_issues.append(f"{js_file}: отсутствуют функции {missing_functions}")
    
    if content_issues:
        print("❌ Проблемы с содержимым JS файлов:")
        for issue in content_issues:
            print(f"  - {issue}")
        return False
    
    print("✅ Содержимое JS файлов корректно")
    return True


def test_server_startup():
    """Проверяем, что сервер запускается без ошибок"""
    print("🔍 Проверяем запуск сервера...")
    
    try:
        # Проверяем, что сервер отвечает
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print("✅ Сервер запущен и отвечает")
            return True
        else:
            print(f"❌ Сервер отвечает с кодом {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Сервер не отвечает: {e}")
        return False


def test_cms_pages_load():
    """Проверяем, что CMS страницы загружаются"""
    print("🔍 Проверяем загрузку CMS страниц...")
    
    cms_pages = [
        '/cms',
        '/cms/texts',
        '/cms/images', 
        '/cms/seo',
        '/cms/users'
    ]
    
    failed_pages = []
    
    for page in cms_pages:
        try:
            response = requests.get(f'http://localhost:8000{page}', timeout=5)
            if response.status_code not in [200, 302]:  # 302 для редиректов на логин
                failed_pages.append(f"{page}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            failed_pages.append(f"{page}: {e}")
    
    if failed_pages:
        print("❌ Проблемы с загрузкой страниц:")
        for page in failed_pages:
            print(f"  - {page}")
        return False
    
    print("✅ CMS страницы загружаются корректно")
    return True


def test_js_files_syntax():
    """Проверяем синтаксис JS файлов"""
    print("🔍 Проверяем синтаксис JS файлов...")
    
    js_files = [
        'app/static/js/theme.js',
        'app/static/js/texts.js',
        'app/static/js/users.js', 
        'app/static/js/seo.js',
        'app/static/js/images.js'
    ]
    
    syntax_issues = []
    
    for js_file in js_files:
        if not os.path.exists(js_file):
            continue
            
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Простая проверка на базовые синтаксические ошибки
        if content.count('{') != content.count('}'):
            syntax_issues.append(f"{js_file}: несоответствие фигурных скобок")
        
        if content.count('(') != content.count(')'):
            syntax_issues.append(f"{js_file}: несоответствие круглых скобок")
        
        # Проверяем на незакрытые строки
        if content.count('"') % 2 != 0:
            syntax_issues.append(f"{js_file}: незакрытые кавычки")
    
    if syntax_issues:
        print("❌ Синтаксические ошибки в JS файлах:")
        for issue in syntax_issues:
            print(f"  - {issue}")
        return False
    
    print("✅ Синтаксис JS файлов корректен")
    return True


def main():
    """Основная функция теста"""
    print("🚀 Запуск автотеста: Вынос скриптов из HTML в JS файлы")
    print("=" * 60)
    
    tests = [
        ("Проверка наличия JS файлов", test_js_files_exist),
        ("Проверка отсутствия встроенных скриптов", test_html_files_no_inline_scripts),
        ("Проверка подключения JS файлов", test_html_files_include_js),
        ("Проверка содержимого JS файлов", test_js_files_content),
        ("Проверка синтаксиса JS файлов", test_js_files_syntax),
        ("Проверка запуска сервера", test_server_startup),
        ("Проверка загрузки CMS страниц", test_cms_pages_load)
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
        print("🎉 Все тесты пройдены! Скрипты успешно вынесены из HTML в JS файлы.")
        return True
    else:
        print("⚠️  Некоторые тесты провалены. Требуется доработка.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
