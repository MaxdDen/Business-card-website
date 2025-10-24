#!/usr/bin/env python3
"""
Тест только редиректа: Проверка сохранения языка при редиректе
Проверяет только логику редиректа без реальной авторизации
"""

import requests
import sys
import os
from unittest.mock import Mock

# Добавляем путь к проекту
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def test_language_redirect_logic():
    """Тест логики редиректа с сохранением языка"""
    print("🧪 ТЕСТ ЛОГИКИ РЕДИРЕКТА: Проверка сохранения языка...")
    
    # Импортируем функции для тестирования
    from app.auth.routes import get_language_from_url, get_cms_redirect_url
    
    test_cases = [
        # (url_path, expected_lang, expected_redirect)
        ("/en/login", "en", "/cms/en/"),
        ("/ru/login", "ru", "/cms/ru/"),
        ("/ua/login", "ua", "/cms/ua/"),
        ("/en/", "en", "/cms/en/"),
        ("/ru/", "ru", "/cms/ru/"),
        ("/ua/", "ua", "/cms/ua/"),
        ("/en", "en", "/cms/en/"),
        ("/ru", "ru", "/cms/ru/"),
        ("/ua", "ua", "/cms/ua/"),
        ("/login", "en", "/cms/en/"),  # язык по умолчанию
        ("/", "en", "/cms/en/"),       # язык по умолчанию
    ]
    
    results = []
    
    for url_path, expected_lang, expected_redirect in test_cases:
        print(f"\n📝 Тестирование: {url_path}")
        
        try:
            # Создаем мок Request
            mock_request = Mock()
            mock_request.url.path = url_path
            
            # Тестируем определение языка
            detected_lang = get_language_from_url(mock_request)
            print(f"   🔍 Определенный язык: {detected_lang} (ожидалось {expected_lang})")
            
            if detected_lang != expected_lang:
                print(f"   ❌ Неправильное определение языка")
                results.append(f"❌ {url_path}: язык {detected_lang} (ожидалось {expected_lang})")
                continue
            
            # Тестируем генерацию URL редиректа
            redirect_url = get_cms_redirect_url(detected_lang)
            print(f"   🔄 URL редиректа: {redirect_url} (ожидалось {expected_redirect})")
            
            if redirect_url == expected_redirect:
                print(f"   ✅ Редирект работает правильно")
                results.append(f"✅ {url_path}: {detected_lang} -> {redirect_url}")
            else:
                print(f"   ❌ Неправильный редирект")
                results.append(f"❌ {url_path}: {redirect_url} (ожидалось {expected_redirect})")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            results.append(f"❌ {url_path}: Ошибка - {e}")
    
    # Итоговый отчет
    print(f"\n📊 ОТЧЕТ ПО ЛОГИКЕ РЕДИРЕКТА:")
    print(f"{'='*50}")
    
    success_count = sum(1 for result in results if result.startswith("✅"))
    error_count = sum(1 for result in results if result.startswith("❌"))
    total_count = len(results)
    
    for result in results:
        print(f"   {result}")
    
    print(f"\n📈 Результат: {success_count} успешно, {error_count} ошибок из {total_count} тестов")
    
    if success_count == total_count:
        print("🎉 ЛОГИКА РЕДИРЕКТА РАБОТАЕТ ПРАВИЛЬНО!")
        return True
    else:
        print("⚠️  ЛОГИКА РЕДИРЕКТА ИМЕЕТ ПРОБЛЕМЫ")
        return False

def test_middleware_language_detection():
    """Тест определения языка в middleware"""
    print("\n🧪 ТЕСТ MIDDLEWARE: Проверка определения языка...")
    
    from app.site.middleware import LanguageMiddleware
    
    # Создаем middleware
    middleware = LanguageMiddleware(None)
    
    test_cases = [
        # (url_path, expected_lang)
        ("/en/login", "en"),
        ("/ru/login", "ru"),
        ("/ua/login", "ua"),
        ("/en/", "en"),
        ("/ru/", "ru"),
        ("/ua/", "ua"),
        ("/en", "en"),
        ("/ru", "ru"),
        ("/ua", "ua"),
        ("/login", "en"),  # язык по умолчанию
        ("/", "en"),       # язык по умолчанию
    ]
    
    results = []
    
    for url_path, expected_lang in test_cases:
        print(f"   🔍 Тестирование: {url_path}")
        
        try:
            detected_lang = middleware.extract_language_from_url(url_path)
            print(f"      Определенный язык: {detected_lang} (ожидалось {expected_lang})")
            
            if detected_lang == expected_lang:
                print(f"      ✅ Правильно")
                results.append(f"✅ {url_path}: {detected_lang}")
            else:
                print(f"      ❌ Неправильно")
                results.append(f"❌ {url_path}: {detected_lang} (ожидалось {expected_lang})")
                
        except Exception as e:
            print(f"      ❌ Ошибка: {e}")
            results.append(f"❌ {url_path}: Ошибка - {e}")
    
    # Итоговый отчет
    print(f"\n📊 ОТЧЕТ ПО MIDDLEWARE:")
    for result in results:
        print(f"   {result}")
    
    success_count = sum(1 for result in results if result.startswith("✅"))
    total_count = len(results)
    
    print(f"\n📈 Результат: {success_count}/{total_count} тестов пройдено")
    return success_count == total_count

def main():
    """Главная функция теста"""
    print("🚀 ЗАПУСК ТЕСТА ЛОГИКИ РЕДИРЕКТА")
    print("="*50)
    
    try:
        # Тест 1: Логика редиректа
        test1_result = test_language_redirect_logic()
        
        # Тест 2: Middleware
        test2_result = test_middleware_language_detection()
        
        # Общий результат
        print(f"\n🎯 ОБЩИЙ РЕЗУЛЬТАТ:")
        print(f"{'='*30}")
        
        if test1_result and test2_result:
            print("🎉 ВСЕ ТЕСТЫ ЛОГИКИ ПРОЙДЕНЫ УСПЕШНО!")
            print("✅ Логика редиректа работает правильно")
            print("✅ Middleware определяет язык правильно")
            print("\n💡 ВЫВОД: Проблема НЕ в логике определения языка и редиректа!")
            print("💡 Проблема может быть в реальной авторизации или настройке сервера")
            return True
        else:
            print("⚠️  НЕКОТОРЫЕ ТЕСТЫ ЛОГИКИ НЕ ПРОЙДЕНЫ")
            if not test1_result:
                print("❌ Проблемы с логикой редиректа")
            if not test2_result:
                print("❌ Проблемы с middleware")
            return False
            
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
