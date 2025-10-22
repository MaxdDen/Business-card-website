#!/usr/bin/env python3
"""
Тест исправленной логики генерации URL
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.site.middleware import _generate_language_urls

def test_fixed_urls():
    """Тест исправленной логики"""
    print("🧪 Тест исправленной логики генерации URL...")
    
    # Тестируем сценарий пользователя
    test_cases = [
        # (current_path, current_language, expected_urls)
        ("/cms/ua/", "ua", {
            "en": "/cms/en/",
            "ru": "/cms/ru/", 
            "ua": "/cms/ua/"
        }),
        ("/cms/ua/texts", "ua", {
            "en": "/cms/en/texts",
            "ru": "/cms/ru/texts",
            "ua": "/cms/ua/texts"
        }),
        ("/cms/en/texts", "en", {
            "en": "/cms/en/texts",
            "ru": "/cms/ru/texts",
            "ua": "/cms/ua/texts"
        }),
        ("/cms/ru/images", "ru", {
            "en": "/cms/en/images",
            "ru": "/cms/ru/images",
            "ua": "/cms/ua/images"
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
        print("🎉 Все тесты исправленной логики прошли успешно!")
        print("✅ Теперь языковые ссылки генерируются правильно!")
    else:
        print("❌ Некоторые тесты провалились")
    
    return all_passed

if __name__ == "__main__":
    success = test_fixed_urls()
    sys.exit(0 if success else 1)
