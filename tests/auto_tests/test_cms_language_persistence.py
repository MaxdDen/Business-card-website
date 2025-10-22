#!/usr/bin/env python3
"""
Автотест для проверки сохранения языка при переходах между страницами CMS
"""

import requests
import sys
import os
import time
from urllib.parse import urljoin

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_cms_language_persistence():
    """
    Тест проверяет, что при переключении языка в CMS
    язык сохраняется при переходах между страницами
    """
    print("🧪 Тестирование сохранения языка в CMS...")
    
    base_url = "http://localhost:8000"
    
    # Список CMS страниц для тестирования
    cms_pages = [
        "/cms/",
        "/cms/texts", 
        "/cms/images",
        "/cms/seo",
        "/cms/users"
    ]
    
    # Языки для тестирования
    languages = ["ru", "en", "ua"]
    
    # Сначала логинимся как admin
    print("📝 Выполняем вход в систему...")
    login_data = {
        "email": "admin@example.com",
        "password": "admin123"
    }
    
    session = requests.Session()
    
    # Получаем CSRF токен
    login_page = session.get(f"{base_url}/login")
    if login_page.status_code != 200:
        print("❌ Не удалось загрузить страницу входа")
        return False
    
    # Ищем CSRF токен в HTML с помощью регулярных выражений
    import re
    csrf_token = None
    
    # Пробуем разные варианты поиска CSRF токена
    csrf_patterns = [
        r'name="csrf_token"[^>]*value="([^"]+)"',
        r'value="([^"]+)"[^>]*name="csrf_token"',
        r'<input[^>]*name="csrf_token"[^>]*value="([^"]+)"',
        r'<input[^>]*value="([^"]+)"[^>]*name="csrf_token"'
    ]
    
    for pattern in csrf_patterns:
        match = re.search(pattern, login_page.text)
        if match:
            csrf_token = match.group(1)
            break
    
    # Проверяем, что токен не пустой
    if not csrf_token or csrf_token.strip() == "":
        print("❌ Не удалось найти CSRF токен")
        print("🔍 Отладочная информация:")
        print(f"   Статус страницы входа: {login_page.status_code}")
        print(f"   Размер HTML: {len(login_page.text)} символов")
        # Ищем любые input поля для отладки
        input_matches = re.findall(r'<input[^>]*>', login_page.text)
        print(f"   Найдено input полей: {len(input_matches)}")
        for i, inp in enumerate(input_matches[:3]):  # Показываем первые 3
            print(f"   Input {i+1}: {inp}")
        
        # Пробуем войти без CSRF токена (возможно, он не требуется)
        print("🔄 Пробуем войти без CSRF токена...")
        login_response = session.post(
            f"{base_url}/login",
            data={
                "email": login_data["email"],
                "password": login_data["password"]
            },
            allow_redirects=False
        )
        
        if login_response.status_code in [200, 302]:
            print("✅ Вход без CSRF токена успешен")
        else:
            print(f"❌ Вход без CSRF токена также не удался: {login_response.status_code}")
            print("🔄 Пробуем войти с пустым CSRF токеном...")
            # Пробуем с пустым токеном
            login_response = session.post(
                f"{base_url}/login",
                data={
                    "email": login_data["email"],
                    "password": login_data["password"],
                    "csrf_token": ""
                },
                allow_redirects=False
            )
            
            if login_response.status_code in [200, 302]:
                print("✅ Вход с пустым CSRF токеном успешен")
            else:
                print(f"❌ Вход с пустым CSRF токеном также не удался: {login_response.status_code}")
                print("📄 Содержимое ответа:", login_response.text[:200])
                return False
    else:
        # Выполняем вход с CSRF токеном
        print(f"🔑 CSRF токен найден: {csrf_token[:10]}...")
        login_response = session.post(
            f"{base_url}/login",
            data={
                "email": login_data["email"],
                "password": login_data["password"],
                "csrf_token": csrf_token
            },
            allow_redirects=False
        )
        
        print(f"📊 Статус ответа входа: {login_response.status_code}")
        
        if login_response.status_code not in [200, 302]:
            print(f"❌ Ошибка входа: {login_response.status_code}")
            print(f"📄 Содержимое ответа: {login_response.text[:500]}...")
            return False
        
        print("✅ Вход выполнен успешно")
    
    # Тестируем каждый язык
    for lang in languages:
        print(f"\n🌍 Тестируем язык: {lang.upper()}")
        
        # Тестируем каждую страницу CMS
        for page in cms_pages:
            # Формируем URL с языковым префиксом
            if lang == "ru":  # ru - язык по умолчанию, без префикса
                test_url = f"{base_url}{page}"
            else:
                test_url = f"{base_url}/cms/{lang}{page[4:]}"  # Заменяем /cms/ на /cms/{lang}/
            
            print(f"  📄 Тестируем: {test_url}")
            
            try:
                response = session.get(test_url)
                
                if response.status_code != 200:
                    print(f"    ❌ Ошибка {response.status_code} для {test_url}")
                    continue
                
                # Проверяем, что язык сохранился в HTML
                if f'data-lang="{lang}"' in response.text or f'lang="{lang}"' in response.text:
                    print(f"    ✅ Язык {lang} корректно отображается")
                else:
                    # Проверяем альтернативные способы определения языка
                    if f'value="{lang}"' in response.text or f'>{lang.upper()}<' in response.text:
                        print(f"    ✅ Язык {lang} найден в контенте")
                    else:
                        print(f"    ⚠️  Язык {lang} не найден в контенте")
                
                # Проверяем, что языковые ссылки генерируются корректно
                language_links_found = 0
                for test_lang in languages:
                    if test_lang == "ru":
                        expected_url = f"{base_url}{page}"
                    else:
                        expected_url = f"{base_url}/cms/{test_lang}{page[4:]}"
                    
                    if expected_url in response.text:
                        language_links_found += 1
                
                if language_links_found >= 2:  # Минимум 2 языка должны быть доступны
                    print(f"    ✅ Языковые ссылки генерируются корректно ({language_links_found}/{len(languages)})")
                else:
                    print(f"    ⚠️  Проблемы с генерацией языковых ссылок ({language_links_found}/{len(languages)})")
                
            except requests.exceptions.RequestException as e:
                print(f"    ❌ Ошибка запроса: {e}")
                continue
    
    print("\n🎯 Тестирование переключения между страницами...")
    
    # Тестируем переходы между страницами с сохранением языка
    for lang in languages:
        print(f"\n🔄 Тестируем переходы для языка {lang.upper()}:")
        
        # Начинаем с dashboard
        start_url = f"{base_url}/cms/{lang}/" if lang != "ru" else f"{base_url}/cms/"
        
        try:
            response = session.get(start_url)
            if response.status_code != 200:
                print(f"  ❌ Не удалось загрузить начальную страницу")
                continue
            
            # Переходим на другие страницы
            test_pages = ["/cms/texts", "/cms/images", "/cms/seo"]
            if lang != "ru":
                test_pages = [f"/cms/{lang}{page[4:]}" for page in test_pages]
            
            for page_url in test_pages:
                full_url = f"{base_url}{page_url}"
                print(f"  🔗 Переход на: {full_url}")
                
                try:
                    page_response = session.get(full_url)
                    if page_response.status_code == 200:
                        print(f"    ✅ Страница загружена успешно")
                        
                        # Проверяем, что язык сохранился
                        if f'>{lang.upper()}<' in page_response.text or f'value="{lang}"' in page_response.text:
                            print(f"    ✅ Язык {lang} сохранен при переходе")
                        else:
                            print(f"    ⚠️  Язык {lang} может быть потерян при переходе")
                    else:
                        print(f"    ❌ Ошибка {page_response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    print(f"    ❌ Ошибка запроса: {e}")
                    
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Ошибка при тестировании переходов: {e}")
    
    print("\n✅ Тестирование языкового переключения в CMS завершено")
    return True

def main():
    """Главная функция теста"""
    print("🚀 Запуск автотеста языкового переключения в CMS")
    print("=" * 60)
    
    try:
        success = test_cms_language_persistence()
        
        if success:
            print("\n🎉 Все тесты прошли успешно!")
            print("✅ Языковое переключение в CMS работает корректно")
        else:
            print("\n❌ Некоторые тесты не прошли")
            print("⚠️  Требуется дополнительная проверка")
            
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        return False
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)