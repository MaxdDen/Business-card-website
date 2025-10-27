#!/usr/bin/env python3
"""
Менеджер запуска автотестов для CMS
Позволяет запускать отдельные тесты или все тесты сразу
"""

import os
import sys
import subprocess
from datetime import datetime

# Путь к папке с тестами
TESTS_DIR = "tests"

# Список доступных тестов
AVAILABLE_TESTS = {
    "csrf": {
        "file": "test_csrf_fix.py",
        "description": "Тест исправления CSRF проблемы"
    },
    "images": {
        "file": "test_images_management.py", 
        "description": "Тест управления изображениями"
    },
    "texts": {
        "file": "test_texts_editor_fixed.py",
        "description": "Тест редактора текстов (исправленная версия)"
    },
    "seo": {
        "file": "test_seo_management.py",
        "description": "Тест SEO функциональности"
    },
    "users": {
        "file": "test_users_management.py",
        "description": "Тест управления пользователями"
    },
    "public": {
        "file": "test_public_site.py",
        "description": "Тест публичного сайта"
    },
    "multilang": {
        "file": "test_multilang.py",
        "description": "Тест мультиязычности"
    },
    "language_persistence": {
        "file": "test_cms_language_persistence.py",
        "description": "Тест сохранения языка в CMS"
    },
    "language_simple": {
        "file": "test_cms_language_simple.py",
        "description": "Упрощенный тест языковых роутов CMS"
    },
    "language_cookie": {
        "file": "test_language_cookie_persistence.py",
        "description": "Тест cookie-based хранения языка (best practices)"
    },
    "security": {
        "file": "test_security.py",
        "description": "Тест безопасности системы (Этап 12)"
    },
    "build": {
        "file": "test_build_scripts.py",
        "description": "Тест скриптов сборки и развертывания (Этап 13)"
    },
    "js_separation": {
        "file": "test_js_separation.py",
        "description": "Тест выноса скриптов из HTML в отдельные JS файлы"
    },
    "url_structure": {
        "file": "test_url_structure_fix.py",
        "description": "Тест новой структуры URL: домен → язык → страница"
    },
    "auth_language_redirect": {
        "file": "test_auth_language_redirect.py",
        "description": "Тест сохранения языка при переходе с авторизации на дашборд"
    },
    "best_practices_links": {
        "file": "test_best_practices_links.py",
        "description": "Тест исправлений ссылок по best practices"
    },
    "unit": {
        "file": "test_validation.py",
        "description": "Юнит-тесты для утилит валидации"
    },
    "unit_cache": {
        "file": "test_cache.py", 
        "description": "Юнит-тесты для системы кэширования"
    },
    "unit_database": {
        "file": "test_database.py",
        "description": "Юнит-тесты для SQL-слоя"
    },
    "integration_auth": {
        "file": "test_auth.py",
        "description": "Интеграционные тесты аутентификации"
    },
    "integration_crud": {
        "file": "test_crud.py",
        "description": "Интеграционные тесты CRUD операций"
    },
    "lighthouse": {
        "file": "test_lighthouse.py",
        "description": "Тесты производительности Lighthouse (Этап 14)"
    },
    "template_parser": {
        "file": "test_template_parser.py",
        "description": "Тест парсера шаблонов (Этап 3)"
    },
    "template_variables_multilang": {
        "file": "test_template_variables_multilang.py",
        "description": "Тест мультиязычности Template Variables"
    },
    "template_variables_improvements": {
        "file": "test_template_variables_improvements.py",
        "description": "Тест улучшений страницы template_variables"
    },
    "template_variables_structure": {
        "file": "test_template_variables_structure.py",
        "description": "Тест исправленной структуры template_variables"
    },
    "refactored_variables": {
        "file": "test_refactored_variables.py",
        "description": "Тест переделанных переменных в новом формате"
    },
    "dynamic_fields": {
        "file": "test_dynamic_fields.py",
        "description": "Тест динамического наполнения полей"
    },
    "dynamic_save": {
        "file": "test_dynamic_save.py",
        "description": "Тест сохранения динамических полей"
    },
    "public_dynamic": {
        "file": "test_public_dynamic_fields.py",
        "description": "Тест динамических полей на публичных страницах"
    },
    "images_multilang_fix": {
        "file": "test_images_multilang_fix.py",
        "description": "Тест исправления мультиязычности на странице изображений"
    },
    "image_paths_fix": {
        "file": "test_image_paths_fix.py",
        "description": "Тест исправления путей к изображениям"
    },
    "full_sync": {
        "file": "test_full_sync.py",
        "description": "Тест полной синхронизации переменных"
    },
    "dynamic_images_seo": {
        "file": "test_dynamic_images_seo.py",
        "description": "Тест динамических изображений и SEO"
    },
    "dashboard_texts_count_fix": {
        "file": "test_dashboard_texts_count_fix.py",
        "description": "Тест исправления подсчета текстовых переменных в dashboard"
    },
    "session_expiry": {
        "file": "test_session_expiry.py",
        "description": "Тест функциональности истечения сессии"
    },
    "password_fix": {
        "file": "test_password_fix.py",
        "description": "Тест исправления ошибки с длиной пароля в bcrypt"
    },
    "startup_fix": {
        "file": "test_startup_fix.py",
        "description": "Тест исправления ошибки при запуске приложения"
    },
    "no_bcrypt_errors": {
        "file": "test_no_bcrypt_errors.py",
        "description": "Тест отсутствия ошибок bcrypt при запуске"
    },
    "bcrypt_implementation": {
        "file": "test_bcrypt_implementation.py",
        "description": "Тест корректного использования bcrypt по best practices"
    },
    "auth_multilang": {
        "file": "test_auth_multilang.py",
        "description": "Тест мультиязычности страниц авторизации (login/register)"
    },
    "language_links_fix": {
        "file": "test_cms_language_links_fix.py",
        "description": "Тест исправления языковых ссылок в CMS"
    },
    "redirects_fix": {
        "file": "test_cms_redirects_fix.py",
        "description": "Тест исправления редиректов в CMS"
    },
    "auth_language_links": {
        "file": "test_auth_language_links.py",
        "description": "Тест языковых переходов в авторизации"
    },
    "auth_language_persistence": {
        "file": "test_auth_language_persistence.py",
        "description": "Тест сохранения языка при авторизации"
    }
}

def print_header():
    """Вывод заголовка"""
    print("=" * 60)
    print("🧪 МЕНЕДЖЕР АВТОТЕСТОВ CMS")
    print("=" * 60)
    print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def print_help():
    """Вывод справки"""
    print("Использование:")
    print("  python manage_tests.py [команда]")
    print()
    print("Команды:")
    print("  all                    - Запустить все тесты")
    print("  list                   - Показать список доступных тестов")
    print("  <имя_теста>           - Запустить конкретный тест")
    print("  help                   - Показать эту справку")
    print()
    print("Доступные тесты:")
    for test_id, test_info in AVAILABLE_TESTS.items():
        print(f"  {test_id:<12} - {test_info['description']}")
    print()

def list_tests():
    """Показать список доступных тестов"""
    print("📋 ДОСТУПНЫЕ ТЕСТЫ:")
    print("-" * 40)
    for test_id, test_info in AVAILABLE_TESTS.items():
        # Определяем путь к тесту в зависимости от типа
        if test_id.startswith("unit"):
            file_path = os.path.join(TESTS_DIR, "unit_tests", test_info["file"])
        elif test_id.startswith("integration"):
            file_path = os.path.join(TESTS_DIR, "integration_tests", test_info["file"])
        elif test_id == "lighthouse":
            file_path = os.path.join(TESTS_DIR, "performance_tests", test_info["file"])
        else:
            file_path = os.path.join(TESTS_DIR, "auto_tests", test_info["file"])
        
        exists = "✅" if os.path.exists(file_path) else "❌"
        print(f"{exists} {test_id:<20} - {test_info['description']}")
        print(f"    Файл: {test_info['file']}")
    print()

def run_test(test_id):
    """Запустить конкретный тест"""
    if test_id not in AVAILABLE_TESTS:
        print(f"❌ Ошибка: Тест '{test_id}' не найден")
        print("Используйте 'python manage_tests.py list' для просмотра доступных тестов")
        return False
    
    test_info = AVAILABLE_TESTS[test_id]
    
    # Определяем путь к тесту в зависимости от типа
    if test_id.startswith("unit"):
        test_file = os.path.join(TESTS_DIR, "unit_tests", test_info["file"])
    elif test_id.startswith("integration"):
        test_file = os.path.join(TESTS_DIR, "integration_tests", test_info["file"])
    elif test_id == "lighthouse":
        test_file = os.path.join(TESTS_DIR, "performance_tests", test_info["file"])
    else:
        test_file = os.path.join(TESTS_DIR, "auto_tests", test_info["file"])
    
    if not os.path.exists(test_file):
        print(f"❌ Ошибка: Файл теста не найден: {test_file}")
        return False
    
    print(f"🚀 Запуск теста: {test_info['description']}")
    print(f"📁 Файл: {test_info['file']}")
    print("-" * 40)
    
    try:
        # Запускаем тест
        result = subprocess.run([sys.executable, test_file], 
                               capture_output=False, 
                               text=True)
        
        if result.returncode == 0:
            print(f"\n✅ Тест '{test_id}' завершен успешно")
            return True
        else:
            print(f"\n❌ Тест '{test_id}' завершен с ошибкой (код: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"\n❌ Ошибка запуска теста: {str(e)}")
        return False

def run_all_tests():
    """Запустить все тесты"""
    print("🚀 ЗАПУСК ВСЕХ ТЕСТОВ")
    print("=" * 40)
    
    results = {}
    total_tests = len(AVAILABLE_TESTS)
    passed_tests = 0
    
    for test_id, test_info in AVAILABLE_TESTS.items():
        print(f"\n📋 Тест {passed_tests + 1}/{total_tests}: {test_info['description']}")
        print("-" * 50)
        
        success = run_test(test_id)
        results[test_id] = success
        
        if success:
            passed_tests += 1
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)
    
    for test_id, success in results.items():
        status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
        print(f"{status:<12} - {test_id}")
    
    print(f"\n📈 РЕЗУЛЬТАТ: {passed_tests}/{total_tests} тестов пройдено")
    
    if passed_tests == total_tests:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        return True
    else:
        print("⚠️  НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
        return False

def main():
    """Главная функция"""
    print_header()
    
    if len(sys.argv) < 2:
        print_help()
        return True
    
    command = sys.argv[1].lower()
    
    if command == "help":
        print_help()
        return True
    elif command == "list":
        list_tests()
        return True
    elif command == "all":
        return run_all_tests()
    elif command in AVAILABLE_TESTS:
        return run_test(command)
    else:
        print(f"❌ Неизвестная команда: {command}")
        print_help()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
