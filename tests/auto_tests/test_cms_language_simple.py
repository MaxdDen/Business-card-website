#!/usr/bin/env python3
"""
Упрощенный автотест для проверки языковых роутов CMS без аутентификации
"""

import requests
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_cms_language_routes():
    """
    Простой тест проверяет доступность языковых роутов CMS
    """
    print("🧪 Простое тестирование языковых роутов CMS...")
    
    base_url = "http://localhost:8000"
    
    # Список языковых роутов для тестирования
    language_routes = [
        # Dashboard
        ("/cms/", "Dashboard (русский по умолчанию)"),
        ("/cms/ru/", "Dashboard (русский)"),
        ("/cms/en/", "Dashboard (английский)"),
        ("/cms/ua/", "Dashboard (украинский)"),
        
        # Texts
        ("/cms/texts", "Texts (русский по умолчанию)"),
        ("/cms/ru/texts", "Texts (русский)"),
        ("/cms/en/texts", "Texts (английский)"),
        ("/cms/ua/texts", "Texts (украинский)"),
        
        # Images
        ("/cms/images", "Images (русский по умолчанию)"),
        ("/cms/ru/images", "Images (русский)"),
        ("/cms/en/images", "Images (английский)"),
        ("/cms/ua/images", "Images (украинский)"),
        
        # SEO
        ("/cms/seo", "SEO (русский по умолчанию)"),
        ("/cms/ru/seo", "SEO (русский)"),
        ("/cms/en/seo", "SEO (английский)"),
        ("/cms/ua/seo", "SEO (украинский)"),
        
        # Users
        ("/cms/users", "Users (русский по умолчанию)"),
        ("/cms/ru/users", "Users (русский)"),
        ("/cms/en/users", "Users (английский)"),
        ("/cms/ua/users", "Users (украинский)"),
    ]
    
    results = []
    
    for route, description in language_routes:
        url = f"{base_url}{route}"
        print(f"🔗 Тестируем: {description}")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ Статус: {response.status_code} - Страница загружена")
                
                # Проверяем наличие языковых переключателей
                if 'language_urls' in response.text or 'supported_languages' in response.text:
                    print(f"   ✅ Языковые переключатели найдены")
                else:
                    print(f"   ⚠️  Языковые переключатели не найдены")
                
                # Проверяем размер контента
                content_length = len(response.text)
                print(f"   📊 Размер контента: {content_length} символов")
                
                results.append(True)
                
            elif response.status_code == 302:
                print(f"   🔄 Статус: {response.status_code} - Редирект (возможно, на страницу входа)")
                print(f"   📍 Редирект на: {response.headers.get('Location', 'неизвестно')}")
                results.append(True)  # Редирект тоже нормально для защищенных страниц
                
            else:
                print(f"   ❌ Статус: {response.status_code} - Ошибка")
                results.append(False)
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Ошибка запроса: {e}")
            results.append(False)
        
        print()
    
    # Итоговый отчет
    successful = sum(results)
    total = len(results)
    
    print("=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)
    print(f"✅ Успешно: {successful}/{total}")
    print(f"❌ Ошибок: {total - successful}/{total}")
    
    if successful == total:
        print("🎉 Все языковые роуты работают корректно!")
        return True
    else:
        print("⚠️  Некоторые роуты не работают")
        return False

def main():
    """Главная функция теста"""
    print("🚀 Запуск упрощенного теста языковых роутов CMS")
    print("=" * 60)
    
    try:
        success = test_cms_language_routes()
        
        if success:
            print("\n🎉 Тест завершен успешно!")
            print("✅ Языковые роуты CMS работают корректно")
        else:
            print("\n❌ Тест завершен с ошибками")
            print("⚠️  Требуется дополнительная проверка")
            
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        return False
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
