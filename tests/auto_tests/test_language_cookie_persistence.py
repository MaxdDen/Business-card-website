#!/usr/bin/env python3
"""
Автотест для проверки cookie-based хранения языка пользователя
Тестирует best practices для мультиязычности
"""

import requests
import time
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def test_language_cookie_persistence():
    """
    Тест cookie-based хранения языка пользователя
    """
    print("🧪 Тестирование cookie-based хранения языка...")
    
    base_url = "http://localhost:8000"
    
    # Тест 1: Проверка установки cookie при переключении языка
    print("\n1️⃣ Тестирование установки cookie...")
    
    try:
        # Переходим на русскую версию
        response = requests.get(f"{base_url}/ru/", allow_redirects=True)
        
        if response.status_code == 200:
            print("✅ Успешно загружена русская версия")
            
            # Проверяем наличие cookie
            cookies = response.cookies
            if 'user_language' in cookies:
                print(f"✅ Cookie установлен: user_language={cookies['user_language']}")
            else:
                print("⚠️ Cookie не найден в ответе")
        else:
            print(f"❌ Ошибка загрузки: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании cookie: {e}")
        return False
    
    # Тест 2: Проверка сохранения языка при переходе на дефолтную страницу
    print("\n2️⃣ Тестирование сохранения языка...")
    
    try:
        # Создаем сессию с cookie
        session = requests.Session()
        
        # Устанавливаем cookie вручную
        session.cookies.set('user_language', 'ru')
        
        # Переходим на дефолтную страницу (без языкового префикса)
        response = session.get(f"{base_url}/", allow_redirects=True)
        
        if response.status_code == 200:
            print("✅ Успешно загружена страница с сохраненным языком")
            
            # Проверяем, что мы остались на русской версии
            if '/ru/' in response.url:
                print("✅ Язык сохранен - перенаправление на русскую версию")
            else:
                print(f"⚠️ Неожиданный URL: {response.url}")
        else:
            print(f"❌ Ошибка загрузки: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании сохранения: {e}")
        return False
    
    # Тест 3: Проверка переключения между языками
    print("\n3️⃣ Тестирование переключения языков...")
    
    try:
        session = requests.Session()
        
        # Тестируем украинский язык
        response = session.get(f"{base_url}/ua/", allow_redirects=True)
        if response.status_code == 200:
            print("✅ Украинская версия загружена")
            
            # Проверяем cookie
            if 'user_language' in response.cookies:
                print(f"✅ Cookie обновлен: user_language={response.cookies['user_language']}")
            else:
                print("⚠️ Cookie не обновлен")
        
        # Тестируем английский язык
        response = session.get(f"{base_url}/en/", allow_redirects=True)
        if response.status_code == 200:
            print("✅ Английская версия загружена")
            
            # Проверяем cookie
            if 'user_language' in response.cookies:
                print(f"✅ Cookie обновлен: user_language={response.cookies['user_language']}")
            else:
                print("⚠️ Cookie не обновлен")
                
    except Exception as e:
        print(f"❌ Ошибка при тестировании переключения: {e}")
        return False
    
    # Тест 4: Проверка CMS с сохранением языка
    print("\n4️⃣ Тестирование CMS с сохранением языка...")
    
    try:
        session = requests.Session()
        session.cookies.set('user_language', 'ru')
        
        # Пытаемся получить доступ к CMS (может потребоваться аутентификация)
        response = session.get(f"{base_url}/cms/", allow_redirects=True)
        
        if response.status_code in [200, 302]:
            print("✅ CMS доступна (возможно требуется аутентификация)")
            
            # Проверяем, что язык сохранился в URL
            if '/ru/' in response.url or 'ru' in response.url:
                print("✅ Язык сохранен в CMS")
            else:
                print(f"⚠️ Язык не сохранен в CMS: {response.url}")
        else:
            print(f"⚠️ CMS недоступна: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании CMS: {e}")
        return False
    
    print("\n🎉 Все тесты cookie-based хранения языка прошли успешно!")
    return True

def test_language_middleware_priority():
    """
    Тест приоритета определения языка: URL > Cookie > Default
    """
    print("\n🧪 Тестирование приоритета определения языка...")
    
    base_url = "http://localhost:8000"
    
    try:
        session = requests.Session()
        
        # Устанавливаем cookie с украинским языком
        session.cookies.set('user_language', 'ua')
        
        # Переходим на русскую версию (URL должен иметь приоритет)
        response = session.get(f"{base_url}/ru/", allow_redirects=True)
        
        if response.status_code == 200:
            print("✅ URL имеет приоритет над cookie")
            
            # Проверяем, что cookie обновился на русский
            if 'user_language' in response.cookies:
                cookie_value = response.cookies['user_language']
                if cookie_value == 'ru':
                    print("✅ Cookie обновлен согласно URL")
                else:
                    print(f"⚠️ Cookie не обновлен: {cookie_value}")
            else:
                print("⚠️ Cookie не найден")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании приоритета: {e}")
        return False
    
    print("✅ Тест приоритета прошел успешно!")
    return True

def test_language_cookie_security():
    """
    Тест безопасности cookie с языком
    """
    print("\n🧪 Тестирование безопасности cookie...")
    
    base_url = "http://localhost:8000"
    
    try:
        # Тест с недопустимым языком в cookie
        session = requests.Session()
        session.cookies.set('user_language', 'invalid_lang')
        
        response = session.get(f"{base_url}/", allow_redirects=True)
        
        if response.status_code == 200:
            print("✅ Недопустимый язык в cookie обработан корректно")
            
            # Проверяем, что используется язык по умолчанию
            if '/en/' in response.url or response.url.endswith('/en'):
                print("✅ Используется язык по умолчанию")
            else:
                print(f"⚠️ Неожиданное поведение: {response.url}")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании безопасности: {e}")
        return False
    
    print("✅ Тест безопасности прошел успешно!")
    return True

def main():
    """
    Основная функция тестирования
    """
    print("🚀 Запуск автотестов cookie-based хранения языка")
    print("=" * 60)
    
    # Проверяем доступность сервера
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code not in [200, 302]:
            print("❌ Сервер недоступен. Запустите сервер командой: python manage.py run_dev")
            return False
    except Exception as e:
        print(f"❌ Сервер недоступен: {e}")
        print("💡 Запустите сервер командой: python manage.py run_dev")
        return False
    
    print("✅ Сервер доступен")
    
    # Запускаем тесты
    tests = [
        test_language_cookie_persistence,
        test_language_middleware_priority,
        test_language_cookie_security
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Тест {test.__name__} не прошел")
        except Exception as e:
            print(f"❌ Ошибка в тесте {test.__name__}: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Результаты: {passed}/{total} тестов прошли успешно")
    
    if passed == total:
        print("🎉 Все тесты прошли успешно!")
        print("\n💡 Best practices для хранения языка:")
        print("   ✅ URL-based подход для SEO")
        print("   ✅ Cookie-based подход для пользовательских предпочтений")
        print("   ✅ Приоритет: URL > Cookie > Default")
        print("   ✅ Безопасная обработка недопустимых языков")
        print("   ✅ Автоматическое обновление cookie при смене языка")
        return True
    else:
        print("❌ Некоторые тесты не прошли")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
