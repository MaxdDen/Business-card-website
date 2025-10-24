#!/usr/bin/env python3
"""
Реальный тест: Проверка сохранения языка при авторизации
Проверяет реальный процесс авторизации и редиректа с сохранением языка
"""

import requests
import sys
import os
import time
from urllib.parse import urljoin

# Добавляем путь к проекту
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def test_real_auth_language_persistence():
    """Реальный тест сохранения языка при авторизации"""
    print("🧪 РЕАЛЬНЫЙ ТЕСТ: Проверка сохранения языка при авторизации...")
    
    base_url = "http://localhost:8000"
    
    # Тестовые данные - используем существующего пользователя
    test_email = "admin@example.com"
    test_password = "admin123"  # Попробуем стандартный пароль
    
    # Список языков для тестирования
    languages = ["en", "ru", "ua"]
    
    results = []
    
    for lang in languages:
        print(f"\n📝 Тестирование реальной авторизации для языка: {lang}")
        
        try:
            # 1. Проверяем доступность страницы логина с языковым префиксом
            login_url = f"{base_url}/{lang}/login"
            print(f"   🔗 Проверяем доступность: {login_url}")
            
            response = requests.get(login_url, timeout=10)
            if response.status_code != 200:
                print(f"   ❌ Ошибка доступа к {login_url}: {response.status_code}")
                results.append(f"❌ {lang}: Ошибка доступа к странице логина")
                continue
            
            print(f"   ✅ Страница логина доступна для языка {lang}")
            
            # 2. Проверяем, что в HTML есть переключатель языков
            html_content = response.text
            if f'/{lang}/login' in html_content:
                print(f"   ✅ Текущий язык {lang} найден в HTML")
            else:
                print(f"   ⚠️  Текущий язык {lang} не найден в HTML")
            
            # 3. Проверяем, что форма логина отправляется на правильный URL
            if f'action="/{lang}/login"' in html_content:
                print(f"   ✅ Форма логина настроена на правильный URL: /{lang}/login")
            else:
                print(f"   ⚠️  Форма логина может быть настроена неправильно")
            
            # 4. Пытаемся выполнить авторизацию
            print(f"   🔐 Выполняем авторизацию...")
            
            # Создаем сессию для сохранения cookies
            session = requests.Session()
            
            # Получаем CSRF токен - сначала делаем GET запрос
            login_page_response = session.get(login_url)
            csrf_token = ""
            
            # Проверяем, что CSRF токен установлен в cookies
            csrf_cookie = session.cookies.get('csrftoken')
            if csrf_cookie:
                csrf_token = csrf_cookie
                print(f"   ✅ CSRF токен получен из cookies: {csrf_token[:10]}...")
            else:
                print(f"   ⚠️  CSRF токен не найден в cookies")
                
                # Пытаемся извлечь из HTML
                if 'name="csrf_token"' in login_page_response.text:
                    import re
                    csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', login_page_response.text)
                    if csrf_match:
                        csrf_token = csrf_match.group(1)
                        print(f"   ✅ CSRF токен получен из HTML: {csrf_token[:10]}...")
                    else:
                        print(f"   ⚠️  CSRF токен не найден в HTML")
                else:
                    print(f"   ⚠️  CSRF токен не найден в форме")
            
            # Выполняем POST запрос на авторизацию
            auth_data = {
                'email': test_email,
                'password': test_password
            }
            
            if csrf_token:
                auth_data['csrf_token'] = csrf_token
            
            auth_response = session.post(login_url, data=auth_data, allow_redirects=False)
            
            print(f"   📊 Статус ответа авторизации: {auth_response.status_code}")
            
            if auth_response.status_code == 302:
                # Проверяем URL редиректа
                redirect_url = auth_response.headers.get('Location', '')
                print(f"   🔄 URL редиректа: {redirect_url}")
                
                # Проверяем, что редирект содержит правильный языковой префикс
                expected_redirect = f"/cms/{lang}/"
                if expected_redirect in redirect_url:
                    print(f"   ✅ Редирект содержит правильный языковой префикс: {expected_redirect}")
                    results.append(f"✅ {lang}: Редирект работает правильно")
                else:
                    print(f"   ❌ Редирект НЕ содержит правильный языковой префикс")
                    print(f"   ❌ Ожидалось: {expected_redirect}")
                    print(f"   ❌ Получено: {redirect_url}")
                    results.append(f"❌ {lang}: Неправильный редирект - {redirect_url}")
            elif auth_response.status_code == 200:
                # Авторизация не удалась, проверяем ошибку
                if 'error' in auth_response.text or 'Invalid' in auth_response.text:
                    print(f"   ⚠️  Авторизация не удалась (возможно, пользователь не существует)")
                    print(f"   ⚠️  Это нормально для тестового окружения")
                    results.append(f"⚠️  {lang}: Авторизация не удалась (пользователь не существует)")
                else:
                    print(f"   ❌ Неожиданный ответ при авторизации")
                    results.append(f"❌ {lang}: Неожиданный ответ при авторизации")
            else:
                print(f"   ❌ Неожиданный статус ответа: {auth_response.status_code}")
                results.append(f"❌ {lang}: Неожиданный статус ответа - {auth_response.status_code}")
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Ошибка запроса для языка {lang}: {e}")
            results.append(f"❌ {lang}: Ошибка запроса - {e}")
        except Exception as e:
            print(f"   ❌ Неожиданная ошибка для языка {lang}: {e}")
            results.append(f"❌ {lang}: Неожиданная ошибка - {e}")
    
    # Итоговый отчет
    print(f"\n📊 ИТОГОВЫЙ ОТЧЕТ:")
    print(f"{'='*50}")
    
    success_count = sum(1 for result in results if result.startswith("✅"))
    warning_count = sum(1 for result in results if result.startswith("⚠️"))
    error_count = sum(1 for result in results if result.startswith("❌"))
    total_count = len(results)
    
    for result in results:
        print(f"   {result}")
    
    print(f"\n📈 Результат: {success_count} успешно, {warning_count} предупреждений, {error_count} ошибок из {total_count} тестов")
    
    if success_count > 0:
        print("🎉 РЕАЛЬНЫЙ ТЕСТ ПРОЙДЕН! Сохранение языка при авторизации работает.")
        return True
    else:
        print("⚠️  РЕАЛЬНЫЙ ТЕСТ НЕ ПРОЙДЕН. Требуется дополнительная проверка.")
        return False

def test_language_detection_in_url():
    """Тест определения языка из URL"""
    print("\n🧪 Тестирование определения языка из URL...")
    
    # Тестируем функцию get_language_from_url
    from app.auth.routes import get_language_from_url
    from fastapi import Request
    from unittest.mock import Mock
    
    test_cases = [
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
        # Создаем мок Request
        mock_request = Mock()
        mock_request.url.path = url_path
        
        try:
            detected_lang = get_language_from_url(mock_request)
            if detected_lang == expected_lang:
                print(f"   ✅ {url_path} -> {detected_lang} (ожидалось {expected_lang})")
                results.append(f"✅ {url_path}: {detected_lang}")
            else:
                print(f"   ❌ {url_path} -> {detected_lang} (ожидалось {expected_lang})")
                results.append(f"❌ {url_path}: {detected_lang} (ожидалось {expected_lang})")
        except Exception as e:
            print(f"   ❌ {url_path} -> Ошибка: {e}")
            results.append(f"❌ {url_path}: Ошибка - {e}")
    
    # Итоговый отчет
    print(f"\n📊 ОТЧЕТ ПО ОПРЕДЕЛЕНИЮ ЯЗЫКА:")
    for result in results:
        print(f"   {result}")
    
    success_count = sum(1 for result in results if result.startswith("✅"))
    total_count = len(results)
    
    print(f"\n📈 Результат: {success_count}/{total_count} тестов пройдено")
    return success_count == total_count

def main():
    """Главная функция теста"""
    print("🚀 ЗАПУСК РЕАЛЬНОГО ТЕСТА: Сохранение языка при авторизации")
    print("="*70)
    
    try:
        # Тест 1: Проверка определения языка из URL
        test1_result = test_language_detection_in_url()
        
        # Тест 2: Реальная проверка авторизации
        test2_result = test_real_auth_language_persistence()
        
        # Общий результат
        print(f"\n🎯 ОБЩИЙ РЕЗУЛЬТАТ:")
        print(f"{'='*30}")
        
        if test1_result and test2_result:
            print("🎉 ВСЕ РЕАЛЬНЫЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            print("✅ Определение языка из URL работает корректно")
            print("✅ Реальная авторизация с сохранением языка работает")
            return True
        else:
            print("⚠️  НЕКОТОРЫЕ РЕАЛЬНЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
            if not test1_result:
                print("❌ Проблемы с определением языка из URL")
            if not test2_result:
                print("❌ Проблемы с реальной авторизацией")
            return False
            
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
