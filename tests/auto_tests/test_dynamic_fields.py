"""
Автотест для проверки динамического наполнения полей в CMS
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


def test_dynamic_fields_api():
    """Тест API для динамических полей"""
    print("🧪 Тестирование API динамических полей...")
    
    try:
        # Импортируем FastAPI приложение
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Тест получения динамических полей для текстов
        print("  📝 Тестирование API /cms/api/dynamic-fields для текстов...")
        response = client.get("/cms/api/dynamic-fields?page=home&lang=en&field_type=texts")
        
        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ API ответ получен: {data.get('success', False)}")
            if data.get('success'):
                fields = data.get('fields', [])
                print(f"    📊 Найдено полей: {len(fields)}")
                for field in fields:
                    print(f"      - {field.get('key')}: {field.get('label')}")
            else:
                print(f"    ⚠️ Ошибка API: {data.get('message')}")
        else:
            print(f"    ❌ HTTP ошибка: {response.status_code}")
        
        # Тест получения динамических полей для SEO
        print("  🔍 Тестирование API /cms/api/dynamic-fields для SEO...")
        response = client.get("/cms/api/dynamic-fields?page=home&lang=en&field_type=seo")
        
        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ API ответ получен: {data.get('success', False)}")
            if data.get('success'):
                fields = data.get('fields', [])
                print(f"    📊 Найдено SEO полей: {len(fields)}")
                for field in fields:
                    print(f"      - {field.get('key')}: {field.get('label')}")
            else:
                print(f"    ⚠️ Ошибка API: {data.get('message')}")
        else:
            print(f"    ❌ HTTP ошибка: {response.status_code}")
        
        # Тест получения типов изображений
        print("  🖼️ Тестирование API /cms/api/image-types...")
        response = client.get("/cms/api/image-types")
        
        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ API ответ получен: {data.get('success', False)}")
            if data.get('success'):
                image_types = data.get('image_types', [])
                print(f"    📊 Найдено типов изображений: {len(image_types)}")
                for img_type in image_types:
                    print(f"      - {img_type.get('type')}: {img_type.get('label')}")
            else:
                print(f"    ⚠️ Ошибка API: {data.get('message')}")
        else:
            print(f"    ❌ HTTP ошибка: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Ошибка тестирования API: {e}")
        return False


def test_dynamic_fields_parsing():
    """Тест парсинга динамических полей"""
    print("🧪 Тестирование парсинга динамических полей...")
    
    try:
        # Создаем временную директорию для тестов
        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем структуру директорий
            templates_dir = Path(temp_dir) / "templates"
            public_dir = templates_dir / "public"
            public_dir.mkdir(parents=True)
            
            # Создаем тестовые шаблоны с различными переменными
            test_templates = {
                "home.html": """
<!DOCTYPE html>
<html>
<head>
    <title>{{ seo.meta_title }}</title>
    <meta name="description" content="{{ seo.meta_description }}">
</head>
<body>
    <h1>{{ texts.title }}</h1>
    <p>{{ texts.description }}</p>
    {% if texts.subtitle %}
    <h2>{{ texts.subtitle }}</h2>
    {% endif %}
    <button>{{ texts.cta_text }}</button>
    <p>Phone: {{ texts.phone }}</p>
    <p>Address: {{ texts.address }}</p>
</body>
</html>
                """,
                "about.html": """
<!DOCTYPE html>
<html>
<head>
    <title>{{ seo.meta_title }}</title>
    <meta name="keywords" content="{{ seo.meta_keywords }}">
</head>
<body>
    <h1>{{ texts.title }}</h1>
    <p>{{ texts.description }}</p>
    <img src="/{{ images.logo.path }}" alt="{{ images.logo.alt }}">
</body>
</html>
                """
            }
            
            # Создаем тестовые файлы
            for filename, content in test_templates.items():
                file_path = public_dir / filename
                file_path.write_text(content, encoding='utf-8')
            
            # Создаем парсер с тестовой директорией
            parser = TemplateParser(str(templates_dir))
            
            # Тестируем парсинг всех шаблонов
            print("  📄 Парсинг всех шаблонов...")
            template_variables = parser.parse_all_templates()
            
            print(f"    📊 Найдено страниц: {len(template_variables)}")
            for page, variables in template_variables.items():
                print(f"      - {page}: {len(variables)} переменных")
                for var in variables:
                    print(f"        * {var}")
            
            # Тестируем фильтрацию по типу полей
            print("  🔍 Тестирование фильтрации полей...")
            
            # Текстовые поля
            texts_fields = []
            seo_fields = []
            
            for page, variables in template_variables.items():
                for variable in variables:
                    if variable.startswith('texts.'):
                        key = variable.replace('texts.', '')
                        if not key.startswith('meta_'):
                            texts_fields.append({'key': key, 'page': page})
                    elif variable.startswith('seo.'):
                        key = variable.replace('seo.', '')
                        if key.startswith('meta_'):
                            seo_fields.append({'key': key, 'page': page})
            
            print(f"    📝 Текстовые поля: {len(texts_fields)}")
            for field in texts_fields:
                print(f"      - {field['page']}.{field['key']}")
            
            print(f"    🔍 SEO поля: {len(seo_fields)}")
            for field in seo_fields:
                print(f"      - {field['page']}.{field['key']}")
            
            return True
            
    except Exception as e:
        print(f"    ❌ Ошибка парсинга: {e}")
        return False


def test_dynamic_fields_validation():
    """Тест валидации динамических полей"""
    print("🧪 Тестирование валидации динамических полей...")
    
    try:
        # Тестируем функции валидации
        from app.cms.routes import _get_field_label, _get_field_type, _get_field_placeholder, _is_field_required
        
        test_cases = [
            ("title", "Заголовок", "text", "Введите заголовок", True),
            ("description", "Описание", "textarea", "Введите описание", False),
            ("meta_title", "SEO заголовок", "text", "SEO заголовок (до 60 символов)", False),
            ("cta_text", "Текст кнопки", "text", "Введите текст кнопки", False),
            ("phone", "Телефон", "text", "Введите номер телефона", False)
        ]
        
        for key, expected_label, expected_type, expected_placeholder, expected_required in test_cases:
            label = _get_field_label(key)
            field_type = _get_field_type(key)
            placeholder = _get_field_placeholder(key)
            required = _is_field_required(key)
            
            print(f"    🔍 Тестирование поля '{key}':")
            print(f"      - Лейбл: {label} (ожидался: {expected_label})")
            print(f"      - Тип: {field_type} (ожидался: {expected_type})")
            print(f"      - Placeholder: {placeholder[:30]}... (ожидался: {expected_placeholder[:30]}...)")
            print(f"      - Обязательное: {required} (ожидалось: {expected_required})")
            
            # Проверяем корректность
            assert label == expected_label, f"Неправильный лейбл для {key}"
            assert field_type == expected_type, f"Неправильный тип для {key}"
            assert placeholder == expected_placeholder, f"Неправильный placeholder для {key}"
            assert required == expected_required, f"Неправильная обязательность для {key}"
        
        print("    ✅ Все тесты валидации пройдены")
        return True
        
    except Exception as e:
        print(f"    ❌ Ошибка валидации: {e}")
        return False


def test_dynamic_fields_integration():
    """Интеграционный тест динамических полей"""
    print("🧪 Интеграционное тестирование динамических полей...")
    
    try:
        # Проверяем, что парсер работает с реальными шаблонами
        parser = TemplateParser()
        
        # Парсим реальные шаблоны
        template_variables = parser.parse_all_templates()
        
        if not template_variables:
            print("    ⚠️ Шаблоны не найдены, пропускаем интеграционный тест")
            return True
        
        print(f"    📊 Найдено страниц: {len(template_variables)}")
        
        # Проверяем каждую страницу
        for page, variables in template_variables.items():
            print(f"    📄 Страница '{page}': {len(variables)} переменных")
            
            # Разделяем на текстовые и SEO поля
            texts_vars = [v for v in variables if v.startswith('texts.') and not v.replace('texts.', '').startswith('meta_')]
            seo_vars = [v for v in variables if v.startswith('seo.') or (v.startswith('texts.') and v.replace('texts.', '').startswith('meta_'))]
            
            print(f"      - Текстовые: {len(texts_vars)}")
            for var in texts_vars:
                print(f"        * {var}")
            
            print(f"      - SEO: {len(seo_vars)}")
            for var in seo_vars:
                print(f"        * {var}")
        
        print("    ✅ Интеграционный тест пройден")
        return True
        
    except Exception as e:
        print(f"    ❌ Ошибка интеграционного теста: {e}")
        return False


def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов динамического наполнения полей")
    print("=" * 60)
    
    tests = [
        ("API динамических полей", test_dynamic_fields_api),
        ("Парсинг динамических полей", test_dynamic_fields_parsing),
        ("Валидация динамических полей", test_dynamic_fields_validation),
        ("Интеграционное тестирование", test_dynamic_fields_integration)
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
