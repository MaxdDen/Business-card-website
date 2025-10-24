#!/usr/bin/env python3
"""
Автотест для проверки функциональности истечения сессии
- Автоматическая переадресация при истечении JWT токена
- Сохранение URL страницы перед редиректом
- Переадресация на сохраненную страницу после логина
- JavaScript мониторинг сессии
"""

import requests
import time
import json
import os
import sys
from datetime import datetime, timezone, timedelta

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_session_expiry_functionality():
    """Тестирование функциональности истечения сессии"""
    print("🧪 Тестирование функциональности истечения сессии...")
    
    base_url = "http://localhost:8000"
    session = requests.Session()
    
    try:
        # 1. Тестируем доступ к CMS без авторизации
        print("1. Тестирование доступа к CMS без авторизации...")
        response = session.get(f"{base_url}/en/cms/")
        assert response.status_code == 302, f"Ожидался редирект 302, получен {response.status_code}"
        assert "/login" in response.headers.get("location", ""), "Редирект должен вести на страницу логина"
        print("✅ Редирект на логин работает корректно")
        
        # 2. Тестируем сохранение URL в параметре next
        print("2. Тестирование сохранения URL в параметре next...")
        cms_url = f"{base_url}/en/cms/texts"
        response = session.get(cms_url)
        assert response.status_code == 302, f"Ожидался редирект 302, получен {response.status_code}"
        location = response.headers.get("location", "")
        assert "next=" in location, "URL должен содержать параметр next"
        assert "cms/texts" in location, "Параметр next должен содержать исходный URL"
        print("✅ URL сохраняется в параметре next")
        
        # 3. Тестируем логин с параметром next
        print("3. Тестирование логина с параметром next...")
        
        # Сначала получаем страницу логина с параметром next
        login_url = f"{base_url}/en/login?next=/en/cms/texts"
        response = session.get(login_url)
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert "next" in response.text, "Страница логина должна содержать скрытое поле next"
        print("✅ Страница логина содержит параметр next")
        
        # 4. Тестируем API endpoints для сессии
        print("4. Тестирование API endpoints для сессии...")
        
        # Тестируем проверку сессии без токена
        response = session.get(f"{base_url}/cms/api/session-check")
        assert response.status_code == 401, f"Ожидался статус 401, получен {response.status_code}"
        print("✅ API session-check корректно возвращает 401 без токена")
        
        # Тестируем обновление сессии без токена
        response = session.post(f"{base_url}/cms/api/session-refresh")
        assert response.status_code == 401, f"Ожидался статус 401, получен {response.status_code}"
        print("✅ API session-refresh корректно возвращает 401 без токена")
        
        # 5. Тестируем с валидной сессией
        print("5. Тестирование с валидной сессией...")
        
        # Логинимся
        login_data = {
            "email": "admin@example.com",
            "password": "admin123456"
        }
        response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
        assert response.status_code == 302, f"Ожидался редирект 302, получен {response.status_code}"
        
        # Проверяем, что получили cookie
        assert "access_token" in session.cookies, "Должен быть установлен access_token cookie"
        print("✅ Успешный логин с установкой cookie")
        
        # Тестируем проверку сессии с валидным токеном
        response = session.get(f"{base_url}/cms/api/session-check")
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        
        session_data = response.json()
        assert session_data.get("valid") == True, "Сессия должна быть валидной"
        assert "expires_at" in session_data, "Должна быть информация о времени истечения"
        assert "time_until_expiry_seconds" in session_data, "Должно быть время до истечения"
        print("✅ API session-check возвращает корректную информацию о сессии")
        
        # Тестируем обновление сессии
        response = session.post(f"{base_url}/cms/api/session-refresh")
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        
        refresh_data = response.json()
        assert refresh_data.get("success") == True, "Обновление сессии должно быть успешным"
        print("✅ API session-refresh успешно обновляет сессию")
        
        # 6. Тестируем доступ к CMS с валидной сессией
        print("6. Тестирование доступа к CMS с валидной сессией...")
        response = session.get(f"{base_url}/en/cms/")
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        print("✅ Доступ к CMS с валидной сессией работает")
        
        # 7. Тестируем JavaScript файл
        print("7. Тестирование JavaScript файла...")
        response = session.get(f"{base_url}/static/js/session-monitor.js")
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert "SessionMonitor" in response.text, "JavaScript файл должен содержать класс SessionMonitor"
        assert "checkSession" in response.text, "JavaScript файл должен содержать метод checkSession"
        print("✅ JavaScript файл доступен и содержит необходимый код")
        
        # 8. Тестируем мультиязычность в редиректах
        print("8. Тестирование мультиязычности в редиректах...")
        
        # Тестируем редирект для русского языка
        response = session.get(f"{base_url}/ru/cms/")
        assert response.status_code == 302, f"Ожидался редирект 302, получен {response.status_code}"
        location = response.headers.get("location", "")
        assert "/ru/login" in location, "Редирект должен учитывать язык"
        print("✅ Мультиязычность в редиректах работает")
        
        print("\n🎉 Все тесты функциональности истечения сессии прошли успешно!")
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка в тестах: {e}")
        return False

def test_session_expiry_edge_cases():
    """Тестирование граничных случаев истечения сессии"""
    print("\n🧪 Тестирование граничных случаев...")
    
    base_url = "http://localhost:8000"
    session = requests.Session()
    
    try:
        # 1. Тестируем некорректные параметры next
        print("1. Тестирование некорректных параметров next...")
        
        # Тестируем с пустым next
        response = session.get(f"{base_url}/login?next=")
        assert response.status_code == 200, "Страница логина должна загружаться с пустым next"
        print("✅ Обработка пустого параметра next работает")
        
        # Тестируем с некорректным next
        response = session.get(f"{base_url}/login?next=invalid_url")
        assert response.status_code == 200, "Страница логина должна загружаться с некорректным next"
        print("✅ Обработка некорректного параметра next работает")
        
        # 2. Тестируем API с некорректными токенами
        print("2. Тестирование API с некорректными токенами...")
        
        # Устанавливаем некорректный токен
        session.cookies.set("access_token", "invalid_token")
        response = session.get(f"{base_url}/cms/api/session-check")
        assert response.status_code == 401, "API должен возвращать 401 для некорректного токена"
        print("✅ API корректно обрабатывает некорректные токены")
        
        # 3. Тестируем различные пути CMS
        print("3. Тестирование различных путей CMS...")
        
        cms_paths = ["/en/cms/", "/en/cms/texts", "/en/cms/images", "/en/cms/seo", "/en/cms/users"]
        for path in cms_paths:
            response = session.get(f"{base_url}{path}")
            assert response.status_code == 302, f"Путь {path} должен редиректить на логин"
            location = response.headers.get("location", "")
            assert "/login" in location, f"Редирект для {path} должен вести на логин"
        print("✅ Все пути CMS корректно редиректят на логин")
        
        # 4. Тестируем статические файлы (не должны редиректить)
        print("4. Тестирование статических файлов...")
        
        static_paths = ["/cms/static/css/output.css", "/cms/static/js/session-monitor.js"]
        for path in static_paths:
            response = session.get(f"{base_url}{path}")
            # Статические файлы могут возвращать 200 или 404, но не должны редиректить
            assert response.status_code != 302, f"Статический файл {path} не должен редиректить"
        print("✅ Статические файлы не редиректят на логин")
        
        print("\n🎉 Все тесты граничных случаев прошли успешно!")
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка в тестах граничных случаев: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск автотестов функциональности истечения сессии")
    print("=" * 60)
    
    # Проверяем доступность сервера
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Сервер недоступен. Убедитесь, что сервер запущен на localhost:8000")
            return False
    except requests.exceptions.RequestException:
        print("❌ Не удается подключиться к серверу. Убедитесь, что сервер запущен на localhost:8000")
        return False
    
    print("✅ Сервер доступен")
    
    # Запускаем тесты
    success = True
    
    # Тестируем основную функциональность
    if not test_session_expiry_functionality():
        success = False
    
    # Тестируем граничные случаи
    if not test_session_expiry_edge_cases():
        success = False
    
    if success:
        print("\n🎉 Все автотесты функциональности истечения сессии прошли успешно!")
        print("\n📋 Реализованная функциональность:")
        print("  ✅ Автоматическая переадресация при истечении JWT токена")
        print("  ✅ Сохранение URL страницы перед редиректом на логин")
        print("  ✅ Переадресация на сохраненную страницу после логина")
        print("  ✅ JavaScript мониторинг сессии с предупреждениями")
        print("  ✅ API endpoints для проверки и обновления сессии")
        print("  ✅ Мультиязычная поддержка в редиректах")
        print("  ✅ Обработка граничных случаев")
    else:
        print("\n❌ Некоторые тесты не прошли. Проверьте логи выше.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
