#!/usr/bin/env python3
"""
Отладка генерации языковых URL
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.site.middleware import _generate_language_urls

def debug_urls():
    """Отладка генерации URL"""
    print("🔍 Отладка генерации языковых URL...")
    
    # Тестируем разные пути
    test_paths = [
        "/cms/",
        "/cms/texts", 
        "/cms/en/texts",
        "/cms/ua/images"
    ]
    
    for path in test_paths:
        print(f"\n📋 Путь: {path}")
        
        # Тестируем для разных языков
        for lang in ["en", "ua", "ru"]:
            urls = _generate_language_urls(path, lang)
            print(f"   Текущий язык: {lang}")
            for url_lang, url in urls.items():
                print(f"     {url_lang}: {url}")

if __name__ == "__main__":
    debug_urls()
