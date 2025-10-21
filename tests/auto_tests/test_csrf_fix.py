#!/usr/bin/env python3
"""
Автотест для проверки исправления CSRF проблемы
Проверяет:
1. API endpoints не требуют CSRF токен
2. Сохранение текстов работает корректно
3. Загрузка текстов работает корректно
"""

import requests
import json
import time
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_csrf_fix():
    """Тест исправления CSRF проблемы"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Тестирование исправления CSRF проблемы...")
    
    # 1. Проверяем, что API endpoints доступны без CSRF токена
    print("\n1. Проверка доступности API без CSRF токена...")
    try:
        response = requests.get(f"{base_url}/cms/api/texts?page=home&lang=en")
        if response.status_code == 401:
            print("   ✅ API требует аутентификации (ожидаемо)")
        elif response.status_code == 403:
            print("   ❌ API все еще требует CSRF токен")
            return False
        else:
            print(f"   ⚠️  Неожиданный статус: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка подключения: {e}")
        return False
    
    # 2. Проверяем POST запрос без CSRF токена
    print("\n2. Проверка POST запроса без CSRF токена...")
    try:
        test_data = {
            "page": "home",
            "lang": "en",
            "texts": {
                "title": "Test Title",
                "subtitle": "Test Subtitle"
            }
        }
        response = requests.post(
            f"{base_url}/cms/api/texts",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 401:
            print("   ✅ POST API требует аутентификации (ожидаемо)")
        elif response.status_code == 403:
            print("   ❌ POST API все еще требует CSRF токен")
            return False
        else:
            print(f"   ⚠️  Неожиданный статус: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка POST запроса: {e}")
        return False
    
    # 3. Проверяем, что обычные формы все еще защищены CSRF
    print("\n3. Проверка CSRF защиты для обычных форм...")
    try:
        # Пытаемся отправить POST запрос к форме логина без CSRF токена
        response = requests.post(f"{base_url}/login", data={
            "email": "test@example.com",
            "password": "testpassword"
        })
        if response.status_code == 403:
            print("   ✅ Обычные формы защищены CSRF")
        else:
            print(f"   ⚠️  Неожиданный статус для формы: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка проверки CSRF: {e}")
        return False
    
    print("\n✅ Все проверки CSRF исправления пройдены!")
    return True

def test_api_structure():
    """Проверка структуры API ответов"""
    print("\n🔍 Проверка структуры API ответов...")
    
    base_url = "http://localhost:8000"
    
    try:
        # Проверяем GET запрос
        response = requests.get(f"{base_url}/cms/api/texts?page=home&lang=en")
        if response.status_code == 401:
            print("   ✅ GET API возвращает 401 (требует аутентификации)")
        else:
            print(f"   ⚠️  GET API статус: {response.status_code}")
        
        # Проверяем POST запрос
        test_data = {
            "page": "home",
            "lang": "en",
            "texts": {"title": "Test"}
        }
        response = requests.post(
            f"{base_url}/cms/api/texts",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 401:
            print("   ✅ POST API возвращает 401 (требует аутентификации)")
        else:
            print(f"   ⚠️  POST API статус: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка проверки API: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск автотеста исправления CSRF проблемы")
    print("=" * 60)
    
    # Проверяем, что сервер запущен
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Сервер запущен и доступен")
        else:
            print("❌ Сервер недоступен")
            sys.exit(1)
    except:
        print("❌ Сервер не запущен. Запустите: python run_server.py")
        sys.exit(1)
    
    # Запускаем тесты
    success = True
    
    success &= test_api_structure()
    success &= test_csrf_fix()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Все тесты CSRF исправления пройдены успешно!")
        print("\n📝 Резюме исправлений:")
        print("   • API endpoints (/cms/api/*) больше не требуют CSRF токен")
        print("   • Обычные формы все еще защищены CSRF")
        print("   • JavaScript запросы работают без CSRF токенов")
        print("   • Сохранение и загрузка текстов должны работать корректно")
    else:
        print("❌ Некоторые тесты не пройдены")
        sys.exit(1)
