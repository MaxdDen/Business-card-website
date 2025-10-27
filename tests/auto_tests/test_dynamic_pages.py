#!/usr/bin/env python3
"""
Автотест для проверки динамического получения списка страниц
"""

import sys
import os
import tempfile
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.utils.template_parser import TemplateParser


def test_get_available_pages():
    """Тест получения списка доступных страниц"""
    print("🧪 Тестирование получения списка доступных страниц...")
    
    try:
        # Получаем список страниц
        pages = TemplateParser.get_available_pages()
        
        print(f"📊 Найдено страниц: {len(pages)}")
        print(f"📋 Страницы: {sorted(pages)}")
        
        # Проверяем, что найдены ожидаемые страницы
        expected_pages = {'home', 'about', 'catalog', 'contacts'}
        found_pages = set(pages)
        
        if expected_pages.issubset(found_pages):
            print("✅ Все ожидаемые страницы найдены!")
        else:
            missing = expected_pages - found_pages
            print(f"❌ Не найдены страницы: {missing}")
            return False
        
        # Проверяем, что base.html исключен
        if 'base' not in pages:
            print("✅ base.html корректно исключен из списка страниц")
        else:
            print("❌ base.html не должен быть в списке страниц")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка получения списка страниц: {e}")
        return False


def test_dynamic_page_detection():
    """Тест динамического определения страниц из путей"""
    print("\n🧪 Тестирование динамического определения страниц...")
    
    try:
        parser = TemplateParser()
        
        # Тестовые пути
        test_paths = [
            "app/templates/public/home.html",
            "app/templates/public/about.html", 
            "app/templates/public/catalog.html",
            "app/templates/public/contacts.html",
            "app/templates/public/base.html",
            "app/templates/public/new_page.html"  # Несуществующая страница
        ]
        
        expected_pages = {
            "app/templates/public/home.html": "home",
            "app/templates/public/about.html": "about",
            "app/templates/public/catalog.html": "catalog", 
            "app/templates/public/contacts.html": "contacts",
            "app/templates/public/base.html": "unknown",  # base должен быть исключен
            "app/templates/public/new_page.html": "new_page"  # Новая страница должна определяться
        }
        
        all_passed = True
        
        for path in test_paths:
            page = parser.get_page_from_path(path)
            expected = expected_pages[path]
            
            if page == expected:
                print(f"✅ {path} -> {page}")
            else:
                print(f"❌ {path} -> ожидалось {expected}, получено {page}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Ошибка тестирования определения страниц: {e}")
        return False


def test_cms_validation():
    """Тест валидации страниц в CMS"""
    print("\n🧪 Тестирование валидации страниц в CMS...")
    
    try:
        # Получаем список страниц как это делается в CMS
        valid_pages = TemplateParser.get_available_pages()
        
        print(f"📊 Доступные страницы для CMS: {sorted(valid_pages)}")
        
        # Тестируем валидацию различных страниц
        test_cases = [
            ("home", True),
            ("about", True), 
            ("catalog", True),
            ("contacts", True),
            ("base", False),  # base не должен быть валидным
            ("nonexistent", False),  # несуществующая страница
            ("", False),  # пустая страница
        ]
        
        all_passed = True
        
        for page, should_be_valid in test_cases:
            is_valid = page in valid_pages
            
            if is_valid == should_be_valid:
                status = "✅" if is_valid else "❌"
                print(f"{status} {page}: {'валидна' if is_valid else 'невалидна'}")
            else:
                print(f"❌ {page}: ожидалось {'валидна' if should_be_valid else 'невалидна'}, получено {'валидна' if is_valid else 'невалидна'}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Ошибка тестирования валидации CMS: {e}")
        return False


def test_new_page_addition():
    """Тест добавления новой страницы"""
    print("\n🧪 Тестирование добавления новой страницы...")
    
    try:
        # Создаем временную папку для тестирования
        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем структуру папок
            public_dir = Path(temp_dir) / "app" / "templates" / "public"
            public_dir.mkdir(parents=True, exist_ok=True)
            
            # Создаем существующие страницы
            existing_pages = ["home.html", "about.html", "catalog.html", "contacts.html", "base.html"]
            for page in existing_pages:
                (public_dir / page).write_text(f"<html><body>{page}</body></html>")
            
            # Получаем список страниц до добавления новой
            pages_before = TemplateParser.get_available_pages(str(Path(temp_dir) / "app" / "templates"))
            print(f"📊 Страницы до добавления: {sorted(pages_before)}")
            
            # Создаем новую страницу
            new_page_content = "<html><body><h1>New Page</h1></body></html>"
            (public_dir / "new_page.html").write_text(new_page_content)
            
            # Получаем список страниц после добавления новой
            pages_after = TemplateParser.get_available_pages(str(Path(temp_dir) / "app" / "templates"))
            print(f"📊 Страницы после добавления: {sorted(pages_after)}")
            
            # Проверяем, что новая страница появилась
            if "new_page" in pages_after and "new_page" not in pages_before:
                print("✅ Новая страница автоматически обнаружена!")
                return True
            else:
                print("❌ Новая страница не обнаружена автоматически")
                return False
        
    except Exception as e:
        print(f"❌ Ошибка тестирования добавления новой страницы: {e}")
        return False


def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов динамического получения страниц")
    print("=" * 60)
    
    tests = [
        test_get_available_pages,
        test_dynamic_page_detection,
        test_cms_validation,
        test_new_page_addition
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✅ Тест пройден")
            else:
                print("❌ Тест провален")
        except Exception as e:
            print(f"❌ Ошибка в тесте {test.__name__}: {e}")
        
        print("-" * 40)
    
    print(f"\n📊 Результаты: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты успешно пройдены!")
        return True
    else:
        print("💥 Некоторые тесты провалены!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
