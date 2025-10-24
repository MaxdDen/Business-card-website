#!/usr/bin/env python3
"""
Отладочный скрипт для проверки реального процесса авторизации
"""

import requests
import sys
import os

def debug_auth_flow():
    """Отладка процесса авторизации"""
    print("🔍 ОТЛАДКА ПРОЦЕССА АВТОРИЗАЦИИ")
    print("="*50)
    
    base_url = "http://localhost:8000"
    
    # Тестовые данные
    test_email = "admin@example.com"
    test_password = "admin123"
    
    # Тестируем разные языки
    languages = ["en", "ru", "ua"]
    
    for lang in languages:
        print(f"\n📝 Тестирование языка: {lang}")
        print("-" * 30)
        
        try:
            # 1. Получаем страницу логина
            login_url = f"{base_url}/{lang}/login"
            print(f"🔗 URL: {login_url}")
            
            session = requests.Session()
            response = session.get(login_url)
            
            print(f"📊 Статус: {response.status_code}")
            print(f"📊 Content-Type: {response.headers.get('content-type', 'unknown')}")
            
            # 2. Проверяем CSRF токен
            csrf_token = session.cookies.get('csrftoken')
            print(f"🍪 CSRF токен: {csrf_token[:10] if csrf_token else 'НЕ НАЙДЕН'}...")
            
            # 3. Проверяем, что язык определяется правильно
            if f'/{lang}/login' in response.text:
                print(f"✅ Язык {lang} найден в HTML")
            else:
                print(f"❌ Язык {lang} НЕ найден в HTML")
            
            # 4. Пытаемся авторизоваться
            print(f"🔐 Попытка авторизации...")
            
            auth_data = {
                'email': test_email,
                'password': test_password,
                'csrf_token': csrf_token
            }
            
            auth_response = session.post(login_url, data=auth_data, allow_redirects=False)
            
            print(f"📊 Статус авторизации: {auth_response.status_code}")
            
            if auth_response.status_code == 302:
                redirect_url = auth_response.headers.get('Location', '')
                print(f"🔄 Редирект: {redirect_url}")
                
                # Проверяем, что редирект содержит правильный язык
                expected_redirect = f"/cms/{lang}/"
                if expected_redirect in redirect_url:
                    print(f"✅ Редирект правильный: {expected_redirect}")
                else:
                    print(f"❌ Редирект неправильный!")
                    print(f"   Ожидалось: {expected_redirect}")
                    print(f"   Получено: {redirect_url}")
                
                # 5. Проверяем, что редирект работает
                print(f"🔍 Проверяем редирект...")
                redirect_response = session.get(f"{base_url}{redirect_url}")
                print(f"📊 Статус редиректа: {redirect_response.status_code}")
                
                if redirect_response.status_code == 200:
                    print(f"✅ Редирект работает")
                    
                    # Проверяем, что на странице dashboard есть правильный язык
                    if f'/{lang}/' in redirect_response.text:
                        print(f"✅ Язык {lang} сохранен на dashboard")
                    else:
                        print(f"❌ Язык {lang} НЕ сохранен на dashboard")
                else:
                    print(f"❌ Редирект не работает")
                    
            elif auth_response.status_code == 401:
                print(f"❌ Авторизация не удалась (401)")
                print(f"   Возможно, неправильный пароль")
            elif auth_response.status_code == 403:
                print(f"❌ CSRF ошибка (403)")
            else:
                print(f"❌ Неожиданный статус: {auth_response.status_code}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()

def check_server_status():
    """Проверка статуса сервера"""
    print("🔍 ПРОВЕРКА СТАТУСА СЕРВЕРА")
    print("="*30)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"✅ Сервер работает: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Сервер не работает: {e}")
        return False

def main():
    """Главная функция"""
    print("🚀 ОТЛАДКА ПРОЦЕССА АВТОРИЗАЦИИ")
    print("="*50)
    
    # Проверяем сервер
    if not check_server_status():
        print("❌ Сервер не работает. Запустите сервер командой: python -m uvicorn app.main:app --reload")
        return False
    
    # Отлаживаем процесс авторизации
    debug_auth_flow()
    
    return True

if __name__ == "__main__":
    main()
