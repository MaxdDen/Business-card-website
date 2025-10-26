"""
Автотест для проверки полной синхронизации переменных
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


def test_full_sync_functionality():
    """Тест функциональности полной синхронизации"""
    print("🧪 Тестирование полной синхронизации переменных...")
    
    try:
        # Создаем парсер
        parser = TemplateParser()
        
        # Парсим шаблоны
        template_variables = parser.parse_all_templates()
        print(f"    📊 Найдено страниц в шаблонах: {len(template_variables)}")
        
        for page, variables in template_variables.items():
            print(f"    📄 {page}: {len(variables)} переменных")
            for var in list(variables)[:5]:  # Показываем первые 5
                print(f"      - {var}")
            if len(variables) > 5:
                print(f"      ... и еще {len(variables) - 5}")
        
        # Тестируем полную синхронизацию
        print("  🔄 Запуск полной синхронизации...")
        results = parser.full_sync_variables_to_database(['en', 'ru', 'ua'])
        
        print(f"    📊 Результаты синхронизации:")
        print(f"      - Обработано страниц: {results['parsed_pages']}")
        print(f"      - Добавлено переменных: {results['added_variables']}")
        print(f"      - Удалено переменных: {results['removed_variables']}")
        print(f"      - Пропущено переменных: {results['skipped_variables']}")
        print(f"      - Ошибок: {results['errors']}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Ошибка тестирования полной синхронизации: {e}")
        return False


def test_database_consistency():
    """Тест согласованности базы данных с шаблонами"""
    print("🧪 Тестирование согласованности БД с шаблонами...")
    
    try:
        # Создаем парсер
        parser = TemplateParser()
        
        # Парсим шаблоны
        template_variables = parser.parse_all_templates()
        
        # Проверяем каждую страницу
        for page, variables in template_variables.items():
            if page == 'unknown':
                continue
                
            print(f"    📄 Проверка страницы {page}...")
            
            # Получаем переменные из БД
            db_results = query_all(
                "SELECT DISTINCT key FROM texts WHERE page = ?",
                (page,)
            )
            db_keys = {row['key'] for row in db_results}
            
            # Получаем переменные из шаблона
            template_keys = set()
            for variable in variables:
                if '.' in variable:
                    key = variable.split('.', 1)[1]
                else:
                    key = variable
                template_keys.add(key)
            
            # Проверяем соответствие
            missing_in_db = template_keys - db_keys
            extra_in_db = db_keys - template_keys
            
            if missing_in_db:
                print(f"      ❌ Отсутствуют в БД: {missing_in_db}")
            else:
                print(f"      ✅ Все переменные из шаблона есть в БД")
            
            if extra_in_db:
                print(f"      ⚠️ Лишние в БД: {extra_in_db}")
            else:
                print(f"      ✅ Нет лишних переменных в БД")
            
            print(f"      📊 Шаблон: {len(template_keys)} переменных, БД: {len(db_keys)} переменных")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Ошибка проверки согласованности: {e}")
        return False


def test_specific_page_sync():
    """Тест синхронизации конкретной страницы"""
    print("🧪 Тестирование синхронизации главной страницы...")
    
    try:
        # Проверяем данные для главной страницы до синхронизации
        print("  📊 Состояние БД до синхронизации:")
        results_before = query_all(
            "SELECT key FROM texts WHERE page = ? ORDER BY key",
            ("home",)
        )
        keys_before = [row['key'] for row in results_before]
        print(f"    🔑 Переменные в БД: {keys_before}")
        
        # Запускаем полную синхронизацию
        parser = TemplateParser()
        sync_results = parser.full_sync_variables_to_database(['en'])
        
        # Проверяем данные после синхронизации
        print("  📊 Состояние БД после синхронизации:")
        results_after = query_all(
            "SELECT key FROM texts WHERE page = ? ORDER BY key",
            ("home",)
        )
        keys_after = [row['key'] for row in results_after]
        print(f"    🔑 Переменные в БД: {keys_after}")
        
        # Сравниваем
        added = set(keys_after) - set(keys_before)
        removed = set(keys_before) - set(keys_after)
        
        if added:
            print(f"    ✅ Добавлено: {added}")
        if removed:
            print(f"    ✅ Удалено: {removed}")
        if not added and not removed:
            print(f"    ✅ Изменений не было")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Ошибка тестирования синхронизации страницы: {e}")
        return False


def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов полной синхронизации переменных")
    print("=" * 60)
    
    tests = [
        ("Функциональность полной синхронизации", test_full_sync_functionality),
        ("Согласованность БД с шаблонами", test_database_consistency),
        ("Синхронизация главной страницы", test_specific_page_sync)
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
