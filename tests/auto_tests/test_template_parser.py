"""
Автотест для проверки работы парсера шаблонов
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


def test_template_parser_basic_functionality():
    """Тест базовой функциональности парсера шаблонов"""
    print("🧪 Тестирование базовой функциональности парсера...")
    
    try:
        # Создаем временную директорию для тестов
        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем структуру директорий
            templates_dir = Path(temp_dir) / "templates"
            public_dir = templates_dir / "public"
            public_dir.mkdir(parents=True)
            
            # Создаем тестовые шаблоны
            test_templates = {
                "home.html": """
<!DOCTYPE html>
<html>
<head>
    <title>{{ seo.title }}</title>
    <meta name="description" content="{{ seo.description }}">
</head>
<body>
    <h1>{{ texts.title }}</h1>
    <p>{{ texts.description }}</p>
    {% if texts.subtitle %}
    <h2>{{ texts.subtitle }}</h2>
    {% endif %}
    <p>Language: {{ lang }}</p>
</body>
</html>
                """,
                "about.html": """
<!DOCTYPE html>
<html>
<head>
    <title>{{ seo.title }}</title>
</head>
<body>
    <h1>{{ texts.title }}</h1>
    <p>{{ texts.content }}</p>
    <p>Phone: {{ texts.phone }}</p>
    <p>Address: {{ texts.address }}</p>
</body>
</html>
                """
            }
            
            # Записываем тестовые файлы
            for filename, content in test_templates.items():
                with open(public_dir / filename, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # Создаем парсер с тестовой директорией
            parser = TemplateParser(str(templates_dir))
            
            # Тест 1: Извлечение переменных из файла
            print("  ✓ Тест извлечения переменных из файла...")
            home_variables = parser.extract_variables_from_file(str(public_dir / "home.html"))
            expected_home = {"seo.title", "seo.description", "texts.title", "texts.description", "texts.subtitle"}
            assert home_variables == expected_home, f"Ожидалось {expected_home}, получено {home_variables}"
            print(f"    Найдено {len(home_variables)} переменных в home.html")
            
            about_variables = parser.extract_variables_from_file(str(public_dir / "about.html"))
            expected_about = {"seo.title", "texts.title", "texts.content", "texts.phone", "texts.address"}
            assert about_variables == expected_about, f"Ожидалось {expected_about}, получено {about_variables}"
            print(f"    Найдено {len(about_variables)} переменных в about.html")
            
            # Тест 2: Определение страницы по пути
            print("  ✓ Тест определения страницы по пути...")
            home_page = parser.get_page_from_path(str(public_dir / "home.html"))
            assert home_page == "home", f"Ожидалось 'home', получено '{home_page}'"
            
            about_page = parser.get_page_from_path(str(public_dir / "about.html"))
            assert about_page == "about", f"Ожидалось 'about', получено '{about_page}'"
            print(f"    Страница home: {home_page}")
            print(f"    Страница about: {about_page}")
            
            # Тест 3: Парсинг всех шаблонов
            print("  ✓ Тест парсинга всех шаблонов...")
            all_variables = parser.parse_all_templates()
            assert "home" in all_variables, "Страница 'home' не найдена"
            assert "about" in all_variables, "Страница 'about' не найдена"
            print(f"    Найдено {len(all_variables)} страниц с переменными")
            
            # Тест 4: Валидация синтаксиса
            print("  ✓ Тест валидации синтаксиса...")
            syntax_issues = parser.validate_template_syntax(str(public_dir / "home.html"))
            assert not syntax_issues['unclosed_tags'], "Найдены незакрытые теги"
            assert not syntax_issues['invalid_syntax'], "Найден некорректный синтаксис"
            print("    Синтаксис шаблонов корректен")
            
            print("✅ Базовая функциональность работает корректно")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка в тесте базовой функциональности: {e}")
        return False


def test_template_parser_variable_filtering():
    """Тест фильтрации переменных"""
    print("🧪 Тестирование фильтрации переменных...")
    
    try:
        parser = TemplateParser()
        
        # Тест системных переменных
        system_vars = ["lang", "request", "supported_languages", "loop.index", "temp"]
        for var in system_vars:
            assert not parser._is_parseable_variable(var), f"Системная переменная {var} не должна парситься"
        
        # Тест переменных без namespace
        no_namespace = ["title", "description", "content"]
        for var in no_namespace:
            assert not parser._is_parseable_variable(var), f"Переменная без namespace {var} не должна парситься"
        
        # Тест поддерживаемых переменных
        valid_vars = ["texts.title", "seo.description", "texts.phone"]
        for var in valid_vars:
            assert parser._is_parseable_variable(var), f"Переменная {var} должна парситься"
        
        # Тест неподдерживаемых namespace
        invalid_vars = ["images.logo", "config.setting", "debug.info"]
        for var in invalid_vars:
            assert not parser._is_parseable_variable(var), f"Переменная {var} не должна парситься"
        
        print("✅ Фильтрация переменных работает корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте фильтрации переменных: {e}")
        return False


def test_template_parser_database_integration():
    """Тест интеграции с базой данных"""
    print("🧪 Тестирование интеграции с базой данных...")
    
    try:
        # Очищаем таблицу texts для чистого теста
        execute("DELETE FROM texts WHERE page IN ('test_home', 'test_about')")
        
        parser = TemplateParser()
        
        # Создаем тестовые данные в БД
        test_data = [
            ("test_home", "title", "en", "Test Home Title"),
            ("test_home", "title", "ru", "Тестовый заголовок"),
            ("test_about", "content", "en", "Test About Content"),
        ]
        
        for page, key, lang, value in test_data:
            execute(
                "INSERT OR REPLACE INTO texts (page, key, lang, value) VALUES (?, ?, ?, ?)",
                (page, key, lang, value)
            )
        
        # Тест получения переменных из БД
        print("  ✓ Тест получения переменных из БД...")
        db_variables = parser.get_database_variables("test_home")
        assert "test_home" in db_variables, "Страница test_home не найдена в БД"
        assert "title" in db_variables["test_home"], "Ключ title не найден"
        assert db_variables["test_home"]["title"]["en"] == "Test Home Title", "Неверное значение для en"
        assert db_variables["test_home"]["title"]["ru"] == "Тестовый заголовок", "Неверное значение для ru"
        print("    Переменные из БД получены корректно")
        
        # Тест получения всех переменных
        all_db_variables = parser.get_database_variables()
        assert "test_home" in all_db_variables, "test_home не найдена в общем списке"
        assert "test_about" in all_db_variables, "test_about не найдена в общем списке"
        print(f"    Найдено {len(all_db_variables)} страниц в БД")
        
        # Очищаем тестовые данные
        execute("DELETE FROM texts WHERE page IN ('test_home', 'test_about')")
        
        print("✅ Интеграция с базой данных работает корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте интеграции с БД: {e}")
        return False


def test_template_parser_sync_functionality():
    """Тест функциональности синхронизации"""
    print("🧪 Тестирование функциональности синхронизации...")
    
    try:
        # Очищаем тестовые данные
        execute("DELETE FROM texts WHERE page = 'test_sync'")
        
        parser = TemplateParser()
        
        # Создаем временный шаблон для теста
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>{{ seo.title }}</title>
</head>
<body>
    <h1>{{ texts.title }}</h1>
    <p>{{ texts.description }}</p>
    <p>{{ texts.new_field }}</p>
</body>
</html>
            """)
            temp_file = f.name
        
        try:
            # Мокаем метод parse_all_templates для возврата тестовых данных
            original_parse_all = parser.parse_all_templates
            parser.parse_all_templates = lambda: {"test_sync": {"seo.title", "texts.title", "texts.description", "texts.new_field"}}
            
            # Тест синхронизации
            print("  ✓ Тест синхронизации переменных...")
            results = parser.sync_variables_to_database(['en', 'ru', 'ua'])
            
            assert results['parsed_pages'] == 1, "Должна быть обработана 1 страница"
            assert results['added_variables'] > 0, "Должны быть добавлены переменные"
            assert results['errors'] == 0, "Не должно быть ошибок"
            print(f"    Синхронизация: {results}")
            
            # Проверяем, что переменные добавлены в БД
            db_vars = parser.get_database_variables("test_sync")
            assert "test_sync" in db_vars, "Страница test_sync не найдена в БД"
            assert "title" in db_vars["test_sync"], "Ключ title не найден"
            assert "description" in db_vars["test_sync"], "Ключ description не найден"
            assert "new_field" in db_vars["test_sync"], "Ключ new_field не найден"
            print("    Переменные успешно добавлены в БД")
            
            # Тест повторной синхронизации (должна пропустить существующие)
            print("  ✓ Тест повторной синхронизации...")
            results2 = parser.sync_variables_to_database(['en', 'ru', 'ua'])
            assert results2['skipped_variables'] > 0, "Должны быть пропущены существующие переменные"
            print(f"    Повторная синхронизация: {results2}")
            
            # Восстанавливаем оригинальный метод
            parser.parse_all_templates = original_parse_all
            
        finally:
            # Очищаем тестовые данные
            execute("DELETE FROM texts WHERE page = 'test_sync'")
            os.unlink(temp_file)
        
        print("✅ Функциональность синхронизации работает корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте синхронизации: {e}")
        return False


def test_template_parser_error_handling():
    """Тест обработки ошибок"""
    print("🧪 Тестирование обработки ошибок...")
    
    try:
        parser = TemplateParser()
        
        # Тест обработки несуществующего файла
        print("  ✓ Тест обработки несуществующего файла...")
        variables = parser.extract_variables_from_file("nonexistent.html")
        assert variables == set(), "Должно возвращаться пустое множество"
        print("    Несуществующий файл обработан корректно")
        
        # Тест обработки некорректного пути
        print("  ✓ Тест обработки некорректного пути...")
        page = parser.get_page_from_path("invalid/path/file.html")
        assert page == "unknown", "Должна возвращаться страница 'unknown'"
        print("    Некорректный путь обработан корректно")
        
        # Тест валидации некорректного синтаксиса
        print("  ✓ Тест валидации некорректного синтаксиса...")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write("""
<!DOCTYPE html>
<html>
<body>
    {% if texts.title %}
    <h1>{{ texts.title }}</h1>
    <!-- Незакрытый тег if -->
    <p>{{ texts.description }}</p>
</body>
</html>
            """)
            temp_file = f.name
        
        try:
            issues = parser.validate_template_syntax(temp_file)
            assert issues['unclosed_tags'], "Должны быть найдены незакрытые теги"
            print("    Некорректный синтаксис обнаружен")
        finally:
            os.unlink(temp_file)
        
        print("✅ Обработка ошибок работает корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте обработки ошибок: {e}")
        return False


def test_template_parser_performance():
    """Тест производительности парсера"""
    print("🧪 Тестирование производительности парсера...")
    
    try:
        import time
        
        parser = TemplateParser()
        
        # Тест времени парсинга
        print("  ✓ Тест времени парсинга...")
        start_time = time.time()
        
        # Парсим реальные шаблоны проекта
        variables = parser.parse_all_templates()
        
        end_time = time.time()
        parse_time = end_time - start_time
        
        print(f"    Время парсинга: {parse_time:.3f} секунд")
        print(f"    Найдено {len(variables)} страниц с переменными")
        
        # Проверяем, что парсинг выполняется достаточно быстро
        assert parse_time < 5.0, f"Парсинг слишком медленный: {parse_time:.3f} секунд"
        
        # Тест времени синхронизации
        print("  ✓ Тест времени синхронизации...")
        start_time = time.time()
        
        results = parser.sync_variables_to_database(['en', 'ru', 'ua'])
        
        end_time = time.time()
        sync_time = end_time - start_time
        
        print(f"    Время синхронизации: {sync_time:.3f} секунд")
        print(f"    Результаты синхронизации: {results}")
        
        # Проверяем, что синхронизация выполняется достаточно быстро
        assert sync_time < 10.0, f"Синхронизация слишком медленная: {sync_time:.3f} секунд"
        
        print("✅ Производительность парсера соответствует требованиям")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте производительности: {e}")
        return False


def main():
    """Основная функция тестирования"""
    print("🚀 Запуск автотестов парсера шаблонов")
    print("=" * 50)
    
    tests = [
        test_template_parser_basic_functionality,
        test_template_parser_variable_filtering,
        test_template_parser_database_integration,
        test_template_parser_sync_functionality,
        test_template_parser_error_handling,
        test_template_parser_performance
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте {test_func.__name__}: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Результаты тестирования:")
    print(f"   ✅ Пройдено: {passed}")
    print(f"   ❌ Провалено: {failed}")
    print(f"   📈 Успешность: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("🎉 Все тесты парсера шаблонов пройдены успешно!")
        return True
    else:
        print("⚠️  Некоторые тесты провалены. Проверьте логи выше.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)