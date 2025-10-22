#!/usr/bin/env python3
"""
Тест для проверки генерации языковых URL в CMS
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.site.middleware import _generate_language_urls

def test_language_url_generation():
    """Тест генерации языковых URL"""
    print("🧪 Тестирование генерации языковых URL...")
    
    # Тестовые случаи
    test_cases = [
        # (current_path, current_language, expected_urls)
        ("/cms/", "ru", {
            "ru": "/cms/",
            "en": "/cms/en/", 
            "ua": "/cms/ua/"
        }),
        ("/cms/", "en", {
            "ru": "/cms/",
            "en": "/cms/en/",
            "ua": "/cms/ua/"
        }),
        ("/cms/texts", "ru", {
            "ru": "/cms/texts",
            "en": "/cms/en/texts",
            "ua": "/cms/ua/texts"
        }),
        ("/cms/en/texts", "en", {
            "ru": "/cms/texts",
            "en": "/cms/en/texts", 
            "ua": "/cms/ua/texts"
        }),
        ("/cms/ua/images", "ua", {
            "ru": "/cms/images",
            "en": "/cms/en/images",
            "ua": "/cms/ua/images"
        }),
        ("/cms/seo", "ru", {
            "ru": "/cms/seo",
            "en": "/cms/en/seo",
            "ua": "/cms/ua/seo"
        })
    ]
    
    all_passed = True
    
    for i, (current_path, current_language, expected) in enumerate(test_cases, 1):
        print(f"\n📋 Тест {i}: {current_path} (язык: {current_language})")
        
        # Генерируем URL
        actual = _generate_language_urls(current_path, current_language)
        
        print(f"   Ожидаемые URL:")
        for lang, url in expected.items():
            print(f"     {lang}: {url}")
        
        print(f"   Фактические URL:")
        for lang, url in actual.items():
            print(f"     {lang}: {url}")
        
        # Проверяем соответствие
        test_passed = True
        for lang in expected:
            if actual.get(lang) != expected[lang]:
                print(f"   ❌ Несоответствие для {lang}: ожидалось {expected[lang]}, получено {actual.get(lang)}")
                test_passed = False
                all_passed = False
        
        if test_passed:
            print(f"   ✅ Тест {i} пройден")
        else:
            print(f"   ❌ Тест {i} провален")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 Все тесты генерации URL прошли успешно!")
    else:
        print("❌ Некоторые тесты провалились")
    
    return all_passed

if __name__ == "__main__":
    success = test_language_url_generation()
    sys.exit(0 if success else 1)
