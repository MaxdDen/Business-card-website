#!/usr/bin/env python3
"""
Автотест для проверки исправления мультиязычности на странице изображений
"""

import os
import sys
import requests
import json
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_images_page_no_scripts():
    """Проверяем, что в разметке images.html нет скриптов"""
    print("🔍 Проверяем отсутствие скриптов в разметке images.html...")
    
    images_template_path = "app/templates/crm/images.html"
    
    if not os.path.exists(images_template_path):
        print(f"❌ Файл {images_template_path} не найден")
        return False
    
    with open(images_template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем, что нет встроенных скриптов с переводами
    if 'window.translations' in content:
        print("❌ Найден встроенный скрипт с переводами в разметке")
        return False
    
    if 'translations = {' in content:
        print("❌ Найден встроенный скрипт с переводами в разметке")
        return False
    
    # Проверяем, что есть только подключение внешнего JS файла
    if '<script src=' not in content:
        print("❌ Не найден подключение внешнего JS файла")
        return False
    
    print("✅ В разметке нет встроенных скриптов с переводами")
    return True

def test_translations_api_endpoint():
    """Проверяем наличие API endpoint для переводов в коде"""
    print("🔍 Проверяем наличие API endpoint для переводов в коде...")
    
    routes_file = "app/cms/routes.py"
    
    if not os.path.exists(routes_file):
        print(f"❌ Файл {routes_file} не найден")
        return False
    
    with open(routes_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем наличие endpoint для переводов
    if '@router.get("/api/translations")' not in content:
        print("❌ API endpoint для переводов не найден в коде")
        return False
    
    if 'get_cms_images_translations' not in content:
        print("❌ Функция get_cms_images_translations не найдена")
        return False
    
    print("✅ API endpoint для переводов присутствует в коде")
    return True

def test_images_api_endpoint():
    """Проверяем наличие API endpoint для изображений в коде"""
    print("🔍 Проверяем наличие API endpoint для изображений в коде...")
    
    routes_file = "app/cms/routes.py"
    
    if not os.path.exists(routes_file):
        print(f"❌ Файл {routes_file} не найден")
        return False
    
    with open(routes_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем наличие endpoint для изображений
    if '@router.get("/api/images")' not in content:
        print("❌ API endpoint для изображений не найден в коде")
        return False
    
    print("✅ API endpoint для изображений присутствует в коде")
    return True

def test_js_file_structure():
    """Проверяем структуру JavaScript файла"""
    print("🔍 Проверяем структуру JavaScript файла...")
    
    js_file_path = "app/static/js/images.js"
    
    if not os.path.exists(js_file_path):
        print(f"❌ Файл {js_file_path} не найден")
        return False
    
    with open(js_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем наличие функции загрузки переводов
    if 'loadTranslations' not in content:
        print("❌ Функция loadTranslations не найдена в JS файле")
        return False
    
    # Проверяем, что используются переводы из переменной translations
    if 'translations.' not in content:
        print("❌ В JS файле не используются переводы из переменной translations")
        return False
    
    # Проверяем, что нет ссылок на window.translations
    if 'window.translations' in content:
        print("❌ В JS файле найдены ссылки на window.translations")
        return False
    
    # Проверяем правильный путь к изображениям
    if '/uploads/${image.path}' not in content:
        print("❌ Не найден правильный путь к изображениям /uploads/")
        return False
    
    print("✅ JavaScript файл имеет правильную структуру")
    return True

def test_database_translations():
    """Проверяем наличие переводов в базе данных"""
    print("🔍 Проверяем наличие переводов в базе данных...")
    
    init_sql_path = "app/database/init.sql"
    
    if not os.path.exists(init_sql_path):
        print(f"❌ Файл {init_sql_path} не найден")
        return False
    
    with open(init_sql_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем наличие переводов для cms_images
    required_keys = [
        'select_file', 'image_uploaded', 'image_deleted', 'move_error'
    ]
    
    for key in required_keys:
        if f"('cms_images', '{key}'" not in content:
            print(f"❌ Не найден перевод для ключа {key} в базе данных")
            return False
    
    print("✅ Все необходимые переводы присутствуют в базе данных")
    return True

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск автотеста исправления мультиязычности на странице изображений")
    print("=" * 70)
    
    tests = [
        ("Отсутствие скриптов в разметке", test_images_page_no_scripts),
        ("API endpoint для переводов", test_translations_api_endpoint),
        ("API endpoint для изображений", test_images_api_endpoint),
        ("Структура JavaScript файла", test_js_file_structure),
        ("Переводы в базе данных", test_database_translations)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Тест: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - ПРОЙДЕН")
            else:
                print(f"❌ {test_name} - ПРОВАЛЕН")
        except Exception as e:
            print(f"💥 {test_name} - ОШИБКА: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 Результаты: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Мультиязычность исправлена по best practices.")
        return True
    else:
        print("⚠️ Некоторые тесты провалены. Требуется дополнительная работа.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
