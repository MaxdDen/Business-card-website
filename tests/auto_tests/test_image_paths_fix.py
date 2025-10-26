#!/usr/bin/env python3
"""
Автотест для проверки исправления путей к изображениям
"""

import os
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_database_paths_structure():
    """Проверяем, что в базе данных сохраняются правильные пути"""
    print("🔍 Проверяем структуру путей в базе данных...")
    
    routes_file = "app/cms/routes.py"
    
    if not os.path.exists(routes_file):
        print(f"❌ Файл {routes_file} не найден")
        return False
    
    with open(routes_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем, что в коде используется правильная структура путей
    if 'os.path.join("optimized"' not in content:
        print("❌ Не найден правильный путь для оптимизированных изображений")
        return False
    
    if 'os.path.join("originals"' not in content:
        print("❌ Не найден правильный путь для оригинальных изображений")
        return False
    
    print("✅ Пути в базе данных настроены правильно")
    return True

def test_templates_image_paths():
    """Проверяем, что в шаблонах используются правильные пути к изображениям"""
    print("🔍 Проверяем пути к изображениям в шаблонах...")
    
    templates_to_check = [
        "app/templates/public/home.html",
        "app/templates/public/base.html"
    ]
    
    for template_path in templates_to_check:
        if not os.path.exists(template_path):
            print(f"❌ Файл {template_path} не найден")
            return False
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем, что используются правильные пути
        if '/uploads/{{' not in content:
            print(f"❌ В шаблоне {template_path} не найдены правильные пути к изображениям")
            return False
        
        # Проверяем, что нет старых путей
        if '/{{' in content and '/uploads/{{' not in content:
            print(f"❌ В шаблоне {template_path} найдены старые пути к изображениям")
            return False
    
    print("✅ Все шаблоны используют правильные пути к изображениям")
    return True

def test_js_image_paths():
    """Проверяем, что в JavaScript используются правильные пути к изображениям"""
    print("🔍 Проверяем пути к изображениям в JavaScript...")
    
    js_file = "app/static/js/images.js"
    
    if not os.path.exists(js_file):
        print(f"❌ Файл {js_file} не найден")
        return False
    
    with open(js_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем, что используется правильный путь
    if '/uploads/${image.path}' not in content:
        print("❌ В JavaScript не найден правильный путь к изображениям")
        return False
    
    print("✅ JavaScript использует правильные пути к изображениям")
    return True

def test_uploads_directory_structure():
    """Проверяем структуру папки uploads"""
    print("🔍 Проверяем структуру папки uploads...")
    
    uploads_dir = "uploads"
    originals_dir = os.path.join(uploads_dir, "originals")
    optimized_dir = os.path.join(uploads_dir, "optimized")
    
    if not os.path.exists(uploads_dir):
        print(f"❌ Папка {uploads_dir} не найдена")
        return False
    
    if not os.path.exists(originals_dir):
        print(f"❌ Папка {originals_dir} не найдена")
        return False
    
    if not os.path.exists(optimized_dir):
        print(f"❌ Папка {optimized_dir} не найдена")
        return False
    
    print("✅ Структура папки uploads правильная")
    return True

def test_image_files_exist():
    """Проверяем, что изображения существуют в правильных папках"""
    print("🔍 Проверяем наличие изображений в папках...")
    
    originals_dir = "uploads/originals"
    optimized_dir = "uploads/optimized"
    
    if not os.path.exists(originals_dir) or not os.path.exists(optimized_dir):
        print("❌ Папки с изображениями не найдены")
        return False
    
    # Проверяем, что есть файлы в обеих папках
    originals_files = os.listdir(originals_dir)
    optimized_files = os.listdir(optimized_dir)
    
    if not originals_files:
        print("❌ В папке originals нет файлов")
        return False
    
    if not optimized_files:
        print("❌ В папке optimized нет файлов")
        return False
    
    # Проверяем, что есть соответствующие файлы
    for orig_file in originals_files:
        if orig_file.endswith('.jpg'):
            webp_file = orig_file.replace('.jpg', '.webp')
            if webp_file not in optimized_files:
                print(f"❌ Не найден оптимизированный файл для {orig_file}")
                return False
    
    print("✅ Изображения существуют в правильных папках")
    return True

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск автотеста исправления путей к изображениям")
    print("=" * 70)
    
    tests = [
        ("Структура путей в базе данных", test_database_paths_structure),
        ("Пути к изображениям в шаблонах", test_templates_image_paths),
        ("Пути к изображениям в JavaScript", test_js_image_paths),
        ("Структура папки uploads", test_uploads_directory_structure),
        ("Наличие изображений в папках", test_image_files_exist)
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
        print("🎉 Все тесты пройдены! Пути к изображениям исправлены.")
        return True
    else:
        print("⚠️ Некоторые тесты провалены. Требуется дополнительная работа.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
