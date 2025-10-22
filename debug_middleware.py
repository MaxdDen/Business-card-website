#!/usr/bin/env python3
"""
Отладка middleware для языковых URL
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.site.middleware import _generate_language_urls

def debug_middleware():
    """Отладка middleware"""
    print("🔍 Отладка генерации языковых URL...")
    
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
        
        urls = _generate_language_urls(current_path, current_language)
        
        print("   Сгенерированные URL:")
        for lang, url in urls.items():
            print(f"     {lang}: {url}")
        
        # Проверяем логику
        print("   Анализ:")
        if current_path.startswith('/cms/'):
            # Определяем базовый путь
            clean_path = current_path
            for lang in ["ru", "en", "ua"]:
                if current_path.startswith(f'/cms/{lang}/'):
                    clean_path = f'/cms{current_path[len(f"/cms/{lang}"):]}'
                    break
                elif current_path == f'/cms/{lang}':
                    clean_path = '/cms/'
                    break
            
            print(f"     Базовый путь: {clean_path}")
            
            # Проверяем правильность генерации
            for lang, url in urls.items():
                if lang == "ru":  # Язык по умолчанию
                    expected = clean_path
                else:
                    if clean_path == '/cms/':
                        expected = f'/cms/{lang}/'
                    else:
                        sub_path = clean_path[4:] if clean_path.startswith('/cms/') else clean_path
                        expected = f'/cms/{lang}{sub_path}'
                
                if url == expected:
                    print(f"     ✅ {lang}: {url} (правильно)")
                else:
                    print(f"     ❌ {lang}: {url} (ожидалось: {expected})")

if __name__ == "__main__":
    debug_middleware()