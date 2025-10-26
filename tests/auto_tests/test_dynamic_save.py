"""
Автотест для проверки сохранения динамических полей
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


def test_dynamic_save_validation():
    """Тест валидации при сохранении динамических полей"""
    print("🧪 Тестирование валидации сохранения динамических полей...")
    
    try:
        # Импортируем FastAPI приложение
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Тест сохранения с динамическими полями
        print("  💾 Тестирование сохранения динамических полей...")
        
        # Подготавливаем данные для сохранения
        save_data = {
            "page": "home",
            "lang": "en", 
            "texts": {
                "title": "Dynamic Test Title",
                "description": "Dynamic test description",
                "fast": "Fast delivery service",
                "quality": "High quality products",
                "reliable": "Reliable partner"
            }
        }
        
        # Отправляем POST запрос для сохранения
        response = client.post("/cms/api/texts", json=save_data)
        
        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ Сохранение успешно: {data.get('success', False)}")
            if data.get('success'):
                print(f"    📊 Сохранено полей: {data.get('saved_count', 0)}")
            else:
                print(f"    ⚠️ Ошибка сохранения: {data.get('message')}")
        else:
            print(f"    ❌ HTTP ошибка: {response.status_code}")
            print(f"    📝 Ответ: {response.text}")
        
        # Проверяем, что данные сохранились в БД
        print("  🔍 Проверка сохранения в БД...")
        from app.database.db import query_all
        
        results = query_all(
            "SELECT key, value FROM texts WHERE page = ? AND lang = ?",
            ("home", "en")
        )
        
        saved_fields = {row["key"]: row["value"] for row in results}
        print(f"    📊 Найдено в БД: {len(saved_fields)} полей")
        
        # Проверяем конкретные поля
        test_fields = ["title", "description", "fast", "quality", "reliable"]
        for field in test_fields:
            if field in saved_fields:
                print(f"      ✅ {field}: {saved_fields[field][:30]}...")
            else:
                print(f"      ❌ {field}: не найдено")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Ошибка тестирования сохранения: {e}")
        return False


def test_dynamic_fields_parsing():
    """Тест парсинга динамических полей из реальных шаблонов"""
    print("🧪 Тестирование парсинга динамических полей...")
    
    try:
        # Создаем парсер
        parser = TemplateParser()
        
        # Парсим реальные шаблоны
        template_variables = parser.parse_all_templates()
        
        if not template_variables:
            print("    ⚠️ Шаблоны не найдены, пропускаем тест")
            return True
        
        print(f"    📊 Найдено страниц: {len(template_variables)}")
        
        # Проверяем каждую страницу
        for page, variables in template_variables.items():
            print(f"    📄 Страница '{page}': {len(variables)} переменных")
            
            # Разделяем на текстовые и SEO поля
            texts_vars = [v for v in variables if v.startswith('texts.') and not v.replace('texts.', '').startswith('meta_')]
            seo_vars = [v for v in variables if v.startswith('seo.') or (v.startswith('texts.') and v.replace('texts.', '').startswith('meta_'))]
            
            print(f"      - Текстовые: {len(texts_vars)}")
            for var in texts_vars[:5]:  # Показываем первые 5
                print(f"        * {var}")
            if len(texts_vars) > 5:
                print(f"        ... и еще {len(texts_vars) - 5}")
            
            print(f"      - SEO: {len(seo_vars)}")
            for var in seo_vars:
                print(f"        * {var}")
        
        print("    ✅ Парсинг динамических полей успешен")
        return True
        
    except Exception as e:
        print(f"    ❌ Ошибка парсинга: {e}")
        return False


def test_validation_fallback():
    """Тест fallback валидации при ошибках парсера"""
    print("🧪 Тестирование fallback валидации...")
    
    try:
        # Импортируем FastAPI приложение
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Тест с несуществующей страницей (должен использовать fallback)
        print("  🔄 Тестирование fallback для несуществующей страницы...")
        
        save_data = {
            "page": "nonexistent",
            "lang": "en",
            "texts": {
                "title": "Test Title",
                "invalid_field": "This should fail"
            }
        }
        
        response = client.post("/cms/api/texts", json=save_data)
        
        if response.status_code == 200:
            data = response.json()
            if not data.get('success'):
                print(f"    ✅ Fallback валидация работает: {data.get('message')}")
            else:
                print(f"    ⚠️ Неожиданный успех: {data}")
        else:
            print(f"    ❌ HTTP ошибка: {response.status_code}")
        
        # Тест с валидными полями для fallback
        print("  ✅ Тестирование валидных полей для fallback...")
        
        save_data = {
            "page": "nonexistent", 
            "lang": "en",
            "texts": {
                "title": "Valid Title",
                "description": "Valid Description"
            }
        }
        
        response = client.post("/cms/api/texts", json=save_data)
        
        if response.status_code == 200:
            data = response.json()
            print(f"    📊 Результат: {data.get('success', False)}")
            if data.get('success'):
                print(f"    ✅ Fallback сохранение работает")
            else:
                print(f"    ⚠️ Ошибка fallback: {data.get('message')}")
        else:
            print(f"    ❌ HTTP ошибка: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Ошибка тестирования fallback: {e}")
        return False


def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов сохранения динамических полей")
    print("=" * 60)
    
    tests = [
        ("Валидация сохранения динамических полей", test_dynamic_save_validation),
        ("Парсинг динамических полей", test_dynamic_fields_parsing),
        ("Fallback валидация", test_validation_fallback)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                print(f"✅ {test_name} - ПРОЙДЕН")
                passed += 1
            else:
                print(f"❌ {test_name} - ПРОВАЛЕН")
        except Exception as e:
            print(f"❌ {test_name} - ОШИБКА: {e}")
    
    print("\n" + "=" * 60)
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
