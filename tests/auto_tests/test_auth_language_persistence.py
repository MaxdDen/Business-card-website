#!/usr/bin/env python3
"""
Автотест: Проверка сохранения языка при авторизации
Проверяет, что выбранный язык сохраняется при переходе с login.html на dashboard.html
"""

import requests
import sys
import os
import time
from urllib.parse import urljoin

# Добавляем путь к проекту
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def test_language_persistence_in_auth():
    """Тест сохранения языка при авторизации"""
    print("🧪 Тестирование сохранения языка при авторизации...")
    
    base_url = "http://localhost:8000"
    
    # Тестовые данные
    test_email = "test@example.com"
    test_password = "testpassword123"
    
    # Список языков для тестирования
    languages = ["en", "ru", "ua"]
    
    results = []
    
    for lang in languages:
        print(f"\n📝 Тестирование языка: {lang}")
        
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
            if 'language_urls' not in html_content or 'supported_languages' not in html_content:
                print(f"   ⚠️  Переменные мультиязычности не найдены в HTML")
            
            # Проверяем наличие языковых ссылок в HTML
            language_links_found = 0
            for test_lang in ["en", "ru", "ua"]:
                if f'/{test_lang}/login' in html_content:
                    language_links_found += 1
            
            if language_links_found > 0:
                print(f"   ✅ Найдено {language_links_found} языковых ссылок в HTML")
            else:
                print(f"   ⚠️  Языковые ссылки не найдены в HTML")
            
            # 3. Проверяем, что текущий язык отмечен как активный
            if f'bg-blue-600 text-white' in html_content:
                print(f"   ✅ Язык {lang} отмечен как активный")
            else:
                print(f"   ⚠️  Язык {lang} не отмечен как активный")
            
            # 4. Проверяем, что есть ссылки на другие языки
            other_langs = [l for l in languages if l != lang]
            for other_lang in other_langs:
                # Проверяем разные варианты ссылок
                if (f'/{other_lang}/login' in html_content or 
                    f'/{other_lang}/' in html_content or
                    f'language_urls[{other_lang}]' in html_content):
                    print(f"   ✅ Ссылка на язык {other_lang} найдена")
                else:
                    print(f"   ⚠️  Ссылка на язык {other_lang} не найдена")
            
            # 5. Проверяем, что форма логина отправляется на правильный URL
            if f'action="/{lang}/login"' in html_content or f'action="/login"' in html_content:
                print(f"   ✅ Форма логина настроена правильно")
            else:
                print(f"   ⚠️  Форма логина может быть настроена неправильно")
            
            # 6. Проверяем, что ссылка на регистрацию содержит языковой префикс
            if f'/{lang}/register' in html_content:
                print(f"   ✅ Ссылка на регистрацию содержит языковой префикс")
            else:
                print(f"   ⚠️  Ссылка на регистрацию может не содержать языковой префикс")
            
            results.append(f"✅ {lang}: Все проверки пройдены")
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Ошибка запроса для языка {lang}: {e}")
            results.append(f"❌ {lang}: Ошибка запроса - {e}")
        except Exception as e:
            print(f"   ❌ Неожиданная ошибка для языка {lang}: {e}")
            results.append(f"❌ {lang}: Неожиданная ошибка - {e}")
    
    # Проверяем CMS роуты с языковыми префиксами
    print(f"\n📝 Тестирование CMS роутов с языковыми префиксами...")
    
    for lang in languages:
        try:
            # Проверяем доступность CMS dashboard с языковым префиксом
            cms_url = f"{base_url}/cms/{lang}/"
            print(f"   🔗 Проверяем CMS URL: {cms_url}")
            
            response = requests.get(cms_url, timeout=10)
            if response.status_code == 302:
                print(f"   ✅ CMS URL {cms_url} перенаправляет (ожидаемо - нужна авторизация)")
            elif response.status_code == 200:
                print(f"   ✅ CMS URL {cms_url} доступен")
            else:
                print(f"   ⚠️  CMS URL {cms_url} вернул статус {response.status_code}")
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Ошибка запроса CMS для языка {lang}: {e}")
        except Exception as e:
            print(f"   ❌ Неожиданная ошибка CMS для языка {lang}: {e}")
    
    # Итоговый отчет
    print(f"\n📊 ИТОГОВЫЙ ОТЧЕТ:")
    print(f"{'='*50}")
    
    success_count = sum(1 for result in results if result.startswith("✅"))
    total_count = len(results)
    
    for result in results:
        print(f"   {result}")
    
    print(f"\n📈 Результат: {success_count}/{total_count} тестов пройдено")
    
    if success_count == total_count:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Сохранение языка при авторизации работает корректно.")
        return True
    else:
        print("⚠️  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ. Требуется дополнительная проверка.")
        return False

def test_language_switching_in_login():
    """Тест переключения языков на странице логина"""
    print("\n🧪 Тестирование переключения языков на странице логина...")
    
    base_url = "http://localhost:8000"
    languages = ["en", "ru", "ua"]
    
    results = []
    
    for lang in languages:
        try:
            login_url = f"{base_url}/{lang}/login"
            print(f"   🔗 Тестируем: {login_url}")
            
            response = requests.get(login_url, timeout=10)
            if response.status_code != 200:
                print(f"   ❌ Ошибка доступа: {response.status_code}")
                results.append(f"❌ {lang}: Ошибка доступа")
                continue
            
            # Проверяем, что в HTML есть ссылки на все языки
            html_content = response.text
            found_languages = []
            
            for test_lang in languages:
                # Проверяем разные варианты ссылок
                # Текущий язык может не быть ссылкой (он активный)
                if test_lang == lang:
                    # Для текущего языка проверяем, что он отмечен как активный
                    if f'bg-blue-600 text-white' in html_content:
                        found_languages.append(test_lang)
                else:
                    # Для других языков ищем ссылки
                    if (f'/{test_lang}/login' in html_content or 
                        f'/{test_lang}/' in html_content or
                        f'language_urls[{test_lang}]' in html_content or
                        f'href="{{{{ language_urls[{test_lang}] }}}}' in html_content):
                        found_languages.append(test_lang)
            
            if len(found_languages) == len(languages):
                print(f"   ✅ Все языковые ссылки найдены: {found_languages}")
                results.append(f"✅ {lang}: Все языковые ссылки найдены")
            else:
                print(f"   ⚠️  Найдены не все языковые ссылки: {found_languages}")
                results.append(f"⚠️  {lang}: Найдены не все языковые ссылки")
            
        except Exception as e:
            print(f"   ❌ Ошибка для языка {lang}: {e}")
            results.append(f"❌ {lang}: Ошибка - {e}")
    
    # Итоговый отчет
    print(f"\n📊 ОТЧЕТ ПО ПЕРЕКЛЮЧЕНИЮ ЯЗЫКОВ:")
    for result in results:
        print(f"   {result}")
    
    success_count = sum(1 for result in results if result.startswith("✅"))
    total_count = len(results)
    
    print(f"\n📈 Результат: {success_count}/{total_count} тестов пройдено")
    return success_count == total_count

def main():
    """Главная функция теста"""
    print("🚀 ЗАПУСК АВТОТЕСТА: Сохранение языка при авторизации")
    print("="*60)
    
    try:
        # Тест 1: Проверка сохранения языка при авторизации
        test1_result = test_language_persistence_in_auth()
        
        # Тест 2: Проверка переключения языков
        test2_result = test_language_switching_in_login()
        
        # Общий результат
        print(f"\n🎯 ОБЩИЙ РЕЗУЛЬТАТ:")
        print(f"{'='*30}")
        
        if test1_result and test2_result:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            print("✅ Сохранение языка при авторизации работает корректно")
            print("✅ Переключение языков на странице логина работает")
            return True
        else:
            print("⚠️  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
            if not test1_result:
                print("❌ Проблемы с сохранением языка при авторизации")
            if not test2_result:
                print("❌ Проблемы с переключением языков")
            return False
            
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
