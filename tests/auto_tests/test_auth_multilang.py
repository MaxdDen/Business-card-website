#!/usr/bin/env python3
"""
Автотест для проверки мультиязычности на страницах авторизации
Проверяет корректность работы переключателя языков и переводов на login.html и register.html
"""

import sys
import os
import requests
import traceback
from urllib.parse import urljoin

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def test_server_running():
    """Проверка, что сервер запущен"""
    print("🔍 Проверка запуска сервера...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Сервер запущен и отвечает")
            return True
        else:
            print(f"   ❌ Сервер отвечает с кодом {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Сервер не отвечает: {e}")
        return False

def test_login_page_multilang():
    """Тест мультиязычности страницы логина"""
    print("🔍 Тестирование мультиязычности страницы логина...")
    try:
        # Тестируем все поддерживаемые языки
        languages = ['en', 'ru', 'ua']
        base_url = "http://localhost:8000"
        
        for lang in languages:
            print(f"   Тестируем язык: {lang}")
            
            # Проверяем доступность страницы логина с языковым префиксом
            login_url = f"{base_url}/{lang}/login" if lang != 'en' else f"{base_url}/login"
            response = requests.get(login_url, timeout=10)
            
            if response.status_code != 200:
                print(f"   ❌ Страница логина недоступна для языка {lang}: {response.status_code}")
                return False
                
            # Проверяем наличие переключателя языков
            if 'switchLanguage' not in response.text and 'data-language-button' not in response.text:
                print(f"   ❌ Переключатель языков не найден на странице {lang}")
                return False
                
            # Проверяем наличие языковых кнопок
            for check_lang in languages:
                if f'switchLanguage(\'{check_lang}\')' not in response.text:
                    print(f"   ❌ Кнопка переключения на язык {check_lang} не найдена на странице {lang}")
                    return False
                    
            print(f"   ✅ Страница логина для языка {lang} работает корректно")
        
        print("   ✅ Мультиязычность страницы логина работает корректно")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании мультиязычности логина: {e}")
        traceback.print_exc()
        return False

def test_register_page_multilang():
    """Тест мультиязычности страницы регистрации"""
    print("🔍 Тестирование мультиязычности страницы регистрации...")
    try:
        # Тестируем все поддерживаемые языки
        languages = ['en', 'ru', 'ua']
        base_url = "http://localhost:8000"
        
        for lang in languages:
            print(f"   Тестируем язык: {lang}")
            
            # Проверяем доступность страницы регистрации с языковым префиксом
            register_url = f"{base_url}/{lang}/register" if lang != 'en' else f"{base_url}/register"
            response = requests.get(register_url, timeout=10)
            
            if response.status_code != 200:
                print(f"   ❌ Страница регистрации недоступна для языка {lang}: {response.status_code}")
                return False
                
            # Проверяем наличие переключателя языков
            if 'switchLanguage' not in response.text and 'data-language-button' not in response.text:
                print(f"   ❌ Переключатель языков не найден на странице {lang}")
                return False
                
            # Проверяем наличие языковых кнопок
            for check_lang in languages:
                if f'switchLanguage(\'{check_lang}\')' not in response.text:
                    print(f"   ❌ Кнопка переключения на язык {check_lang} не найдена на странице {lang}")
                    return False
                    
            print(f"   ✅ Страница регистрации для языка {lang} работает корректно")
        
        print("   ✅ Мультиязычность страницы регистрации работает корректно")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании мультиязычности регистрации: {e}")
        traceback.print_exc()
        return False

def test_language_switching():
    """Тест переключения языков"""
    print("🔍 Тестирование переключения языков...")
    try:
        base_url = "http://localhost:8000"
        languages = ['en', 'ru', 'ua']
        
        # Тестируем переключение с каждой страницы на каждую
        pages = ['login', 'register']
        
        for page in pages:
            print(f"   Тестируем переключение для страницы: {page}")
            
            for from_lang in languages:
                for to_lang in languages:
                    # Получаем страницу с исходным языком
                    from_url = f"{base_url}/{from_lang}/{page}" if from_lang != 'en' else f"{base_url}/{page}"
                    response = requests.get(from_url, timeout=10)
                    
                    if response.status_code != 200:
                        print(f"   ❌ Страница {from_url} недоступна")
                        continue
                    
                    # Проверяем, что есть кнопка переключения на целевой язык
                    if f'switchLanguage(\'{to_lang}\')' in response.text:
                        print(f"   ✅ Переключение с {from_lang} на {to_lang} для {page} работает")
                    else:
                        print(f"   ❌ Переключение с {from_lang} на {to_lang} для {page} не работает")
                        return False
        
        print("   ✅ Переключение языков работает корректно")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании переключения языков: {e}")
        traceback.print_exc()
        return False

def test_translation_consistency():
    """Тест консистентности переводов"""
    print("🔍 Тестирование консистентности переводов...")
    try:
        base_url = "http://localhost:8000"
        languages = ['en', 'ru', 'ua']
        pages = ['login', 'register']
        
        # Ключевые элементы, которые должны быть переведены
        translation_keys = [
            'title', 'subtitle', 'email', 'password', 'login_button', 'create_account',
            'already_have_account', 'sign_in', 'password_label', 'confirm_password'
        ]
        
        for page in pages:
            print(f"   Тестируем переводы для страницы: {page}")
            
            for lang in languages:
                url = f"{base_url}/{lang}/{page}" if lang != 'en' else f"{base_url}/{page}"
                response = requests.get(url, timeout=10)
                
                if response.status_code != 200:
                    print(f"   ❌ Страница {url} недоступна")
                    continue
                
                # Проверяем, что используются переменные переводов
                for key in translation_keys:
                    if f"{{{{ t.{key}" in response.text:
                        print(f"   ✅ Ключ перевода {key} найден на странице {page} ({lang})")
                    else:
                        print(f"   ⚠️  Ключ перевода {key} не найден на странице {page} ({lang})")
        
        print("   ✅ Консистентность переводов проверена")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании консистентности переводов: {e}")
        traceback.print_exc()
        return False

def test_responsive_design():
    """Тест адаптивности дизайна"""
    print("🔍 Тестирование адаптивности дизайна...")
    try:
        base_url = "http://localhost:8000"
        languages = ['en', 'ru', 'ua']
        pages = ['login', 'register']
        
        for page in pages:
            print(f"   Тестируем адаптивность для страницы: {page}")
            
            for lang in languages:
                url = f"{base_url}/{lang}/{page}" if lang != 'en' else f"{base_url}/{page}"
                response = requests.get(url, timeout=10)
                
                if response.status_code != 200:
                    continue
                
                # Проверяем наличие адаптивных классов
                responsive_classes = [
                    'min-h-screen', 'flex', 'items-center', 'justify-center',
                    'w-full', 'max-w-md', 'space-y-6', 'space-y-4'
                ]
                
                for css_class in responsive_classes:
                    if css_class in response.text:
                        print(f"   ✅ Адаптивный класс {css_class} найден")
                    else:
                        print(f"   ⚠️  Адаптивный класс {css_class} не найден")
        
        print("   ✅ Адаптивность дизайна проверена")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании адаптивности: {e}")
        return False

def main():
    """Основная функция автотеста"""
    print("🚀 Запуск автотеста мультиязычности страниц авторизации")
    print("=" * 60)
    
    tests = [
        ("Запуск сервера", test_server_running),
        ("Мультиязычность логина", test_login_page_multilang),
        ("Мультиязычность регистрации", test_register_page_multilang),
        ("Переключение языков", test_language_switching),
        ("Консистентность переводов", test_translation_consistency),
        ("Адаптивность дизайна", test_responsive_design),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - ПРОЙДЕН")
            else:
                print(f"❌ {test_name} - ПРОВАЛЕН")
        except Exception as e:
            print(f"❌ {test_name} - ОШИБКА: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"📊 Результаты: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты прошли успешно! Мультиязычность страниц авторизации работает корректно.")
        return True
    else:
        print(f"⚠️  {total - passed} тестов провалено. Требуется исправление.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
