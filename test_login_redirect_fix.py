#!/usr/bin/env python3
"""
Тест исправления редиректа после логина
Проверяет, что при авторизации на /login происходит редирект на /cms/ (без языкового префикса для английского языка)
"""

import requests
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_login_redirect():
    """Тестирует редирект после логина"""
    base_url = "http://127.0.0.1:8000"
    
    print("🧪 Тестирование исправления редиректа после логина...")
    
    try:
        # 1. Проверяем доступность сервера
        print("1. Проверка доступности сервера...")
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Сервер недоступен")
            return False
        print("✅ Сервер доступен")
        
        # 2. Проверяем страницу логина
        print("2. Проверка страницы логина...")
        response = requests.get(f"{base_url}/login", timeout=5)
        if response.status_code != 200:
            print("❌ Страница логина недоступна")
            return False
        print("✅ Страница логина доступна")
        
        # 3. Проверяем, что в HTML есть правильный next
        if 'name="next"' in response.text:
            # Ищем значение next в HTML
            import re
            next_match = re.search(r'name="next"[^>]*value="([^"]*)"', response.text)
            if next_match:
                next_url = next_match.group(1)
                print(f"📋 Найден next в форме: {next_url}")
                
                # Проверяем, что для английского языка (по умолчанию) next = "/cms/"
                if next_url == "/cms/":
                    print("✅ Редирект настроен правильно: /cms/ (без языкового префикса для английского)")
                    return True
                else:
                    print(f"❌ Неправильный редирект: ожидается '/cms/', получен '{next_url}'")
                    return False
            else:
                print("❌ Не найден next в форме логина")
                return False
        else:
            print("❌ Форма логина не содержит поле next")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_redirect_function():
    """Тестирует функцию get_cms_redirect_url"""
    print("\n🔧 Тестирование функции get_cms_redirect_url...")
    
    try:
        from app.auth.routes import get_cms_redirect_url
        
        # Тест для английского языка (по умолчанию)
        result_en = get_cms_redirect_url("en")
        print(f"📋 get_cms_redirect_url('en') = '{result_en}'")
        if result_en == "/cms/":
            print("✅ Английский язык: правильный редирект без префикса")
        else:
            print(f"❌ Английский язык: ожидается '/cms/', получен '{result_en}'")
            return False
        
        # Тест для русского языка
        result_ru = get_cms_redirect_url("ru")
        print(f"📋 get_cms_redirect_url('ru') = '{result_ru}'")
        if result_ru == "/ru/cms/":
            print("✅ Русский язык: правильный редирект с префиксом")
        else:
            print(f"❌ Русский язык: ожидается '/ru/cms/', получен '{result_ru}'")
            return False
        
        # Тест для украинского языка
        result_ua = get_cms_redirect_url("ua")
        print(f"📋 get_cms_redirect_url('ua') = '{result_ua}'")
        if result_ua == "/ua/cms/":
            print("✅ Украинский язык: правильный редирект с префиксом")
        else:
            print(f"❌ Украинский язык: ожидается '/ua/cms/', получен '{result_ua}'")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования функции: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск тестов исправления редиректа после логина")
    print("=" * 60)
    
    # Тест функции
    function_test_passed = test_redirect_function()
    
    # Тест интеграции (только если сервер запущен)
    integration_test_passed = test_login_redirect()
    
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"🔧 Функция get_cms_redirect_url: {'✅ ПРОЙДЕН' if function_test_passed else '❌ ПРОВАЛЕН'}")
    print(f"🌐 Интеграционный тест: {'✅ ПРОЙДЕН' if integration_test_passed else '❌ ПРОВАЛЕН'}")
    
    if function_test_passed and integration_test_passed:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Исправление работает корректно.")
        print("✅ При авторизации на /login теперь происходит редирект на /cms/ (без языкового префикса для английского языка)")
        sys.exit(0)
    else:
        print("\n❌ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ!")
        sys.exit(1)
