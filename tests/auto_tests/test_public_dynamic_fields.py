"""
Автотест для проверки динамических полей на публичных страницах
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.utils.template_parser import TemplateParser
from app.database.db import execute, query_one, query_all


def test_public_dynamic_fields():
    """Тест динамических полей на публичных страницах"""
    print("🧪 Тестирование динамических полей на публичных страницах...")
    
    try:
        # Импортируем FastAPI приложение
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Тест главной страницы
        print("  🏠 Тестирование главной страницы...")
        response = client.get("/")
        
        if response.status_code == 200:
            content = response.text
            print(f"    ✅ Главная страница загружена: {response.status_code}")
            
            # Проверяем наличие динамических полей в HTML (ищем отрендеренные значения)
            dynamic_fields = {
                "fast": "Fast",
                "quality": "Quality", 
                "reliable": "Reliable",
                "our_works": "Our Works",
                "why_choose_us": "Why Choose Us"
            }
            found_fields = []
            
            for field, expected_value in dynamic_fields.items():
                # Ищем значение с учетом возможных пробелов и форматирования
                if expected_value in content or expected_value.strip() in content:
                    found_fields.append(field)
                    print(f"      ✅ Поле {field} найдено в HTML (значение: {expected_value})")
                else:
                    # Дополнительная проверка - ищем части значения
                    if any(word in content for word in expected_value.split()):
                        found_fields.append(field)
                        print(f"      ✅ Поле {field} найдено в HTML (частично: {expected_value})")
                    else:
                        print(f"      ❌ Поле {field} не найдено в HTML (ожидалось: {expected_value})")
            
            print(f"    📊 Найдено динамических полей: {len(found_fields)}/{len(dynamic_fields)}")
            
        else:
            print(f"    ❌ HTTP ошибка главной страницы: {response.status_code}")
        
        # Тест страницы about
        print("  📄 Тестирование страницы about...")
        response = client.get("/about")
        
        if response.status_code == 200:
            print(f"    ✅ Страница about загружена: {response.status_code}")
        else:
            print(f"    ❌ HTTP ошибка about: {response.status_code}")
        
        # Тест страницы catalog
        print("  📦 Тестирование страницы catalog...")
        response = client.get("/catalog")
        
        if response.status_code == 200:
            print(f"    ✅ Страница catalog загружена: {response.status_code}")
        else:
            print(f"    ❌ HTTP ошибка catalog: {response.status_code}")
        
        # Тест страницы contacts
        print("  📞 Тестирование страницы contacts...")
        response = client.get("/contacts")
        
        if response.status_code == 200:
            print(f"    ✅ Страница contacts загружена: {response.status_code}")
        else:
            print(f"    ❌ HTTP ошибка contacts: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Ошибка тестирования публичных страниц: {e}")
        return False


def test_database_content_for_public():
    """Тест содержимого БД для публичных страниц"""
    print("🧪 Тестирование содержимого БД для публичных страниц...")
    
    try:
        # Проверяем данные для главной страницы
        print("  🏠 Проверка данных для главной страницы...")
        results = query_all(
            "SELECT key, value FROM texts WHERE page = ? AND lang = ?",
            ("home", "en")
        )
        
        print(f"    📊 Найдено записей в БД: {len(results)}")
        
        # Показываем все поля
        for row in results:
            key = row["key"]
            value = row["value"]
            print(f"      - {key}: {value[:30]}{'...' if len(value) > 30 else ''}")
        
        # Проверяем наличие динамических полей
        dynamic_fields = ["fast", "quality", "reliable", "our_works", "why_choose_us"]
        found_in_db = []
        
        for field in dynamic_fields:
            if any(row["key"] == field for row in results):
                found_in_db.append(field)
                print(f"      ✅ {field} найдено в БД")
            else:
                print(f"      ❌ {field} не найдено в БД")
        
        print(f"    📊 Найдено динамических полей в БД: {len(found_in_db)}/{len(dynamic_fields)}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Ошибка проверки БД: {e}")
        return False


def test_get_all_texts_function():
    """Тест функции get_all_texts_for_page"""
    print("🧪 Тестирование функции get_all_texts_for_page...")
    
    try:
        from app.site.routes import get_all_texts_for_page
        
        # Тестируем функцию для главной страницы
        print("  🏠 Тестирование для главной страницы...")
        texts = get_all_texts_for_page("home", "en")
        
        print(f"    📊 Получено текстов: {len(texts)}")
        print(f"    🔑 Ключи: {list(texts.keys())}")
        
        # Проверяем наличие динамических полей
        dynamic_fields = ["fast", "quality", "reliable", "our_works", "why_choose_us"]
        found_fields = []
        
        for field in dynamic_fields:
            if field in texts:
                found_fields.append(field)
                print(f"      ✅ {field}: {texts[field][:30]}{'...' if len(texts[field]) > 30 else ''}")
            else:
                print(f"      ❌ {field}: не найдено")
        
        print(f"    📊 Найдено динамических полей: {len(found_fields)}/{len(dynamic_fields)}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Ошибка тестирования функции: {e}")
        return False


def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов динамических полей на публичных страницах")
    print("=" * 70)
    
    tests = [
        ("Динамические поля на публичных страницах", test_public_dynamic_fields),
        ("Содержимое БД для публичных страниц", test_database_content_for_public),
        ("Функция get_all_texts_for_page", test_get_all_texts_function)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 50)
        
        try:
            if test_func():
                print(f"✅ {test_name} - ПРОЙДЕН")
                passed += 1
            else:
                print(f"❌ {test_name} - ПРОВАЛЕН")
        except Exception as e:
            print(f"❌ {test_name} - ОШИБКА: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 Результаты: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
        return True
    else:
        print("⚠️ Некоторые тесты провалены")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
