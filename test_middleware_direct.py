#!/usr/bin/env python3
"""
Прямой тест middleware для проверки генерации URL
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.site.middleware import _generate_language_urls

def test_direct_middleware():
    """Прямой тест middleware"""
    print("🧪 Прямой тест middleware...")
    
    # Тестируем разные сценарии
    test_cases = [
        ("/cms/", "ru"),
        ("/cms/", "en"), 
        ("/cms/", "ua"),
        ("/cms/texts", "ru"),
        ("/cms/en/texts", "en"),
        ("/cms/ua/images", "ua")
    ]
    
    for current_path, current_language in test_cases:
        print(f"\n📋 Путь: {current_path}, Язык: {current_language}")
        
        try:
            urls = _generate_language_urls(current_path, current_language)
            print(f"   ✅ URL сгенерированы: {urls}")
            
            # Проверяем, что все языки присутствуют
            expected_languages = ["en", "ua", "ru"]
            for lang in expected_languages:
                if lang in urls:
                    print(f"     ✅ {lang}: {urls[lang]}")
                else:
                    print(f"     ❌ {lang}: отсутствует")
                    
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_direct_middleware()
