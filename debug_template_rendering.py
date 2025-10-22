#!/usr/bin/env python3
"""
Отладка рендеринга шаблонов
"""

import requests
import re
import sys
import os

def debug_template_rendering():
    """Отладка рендеринга шаблонов"""
    print("🔍 Отладка рендеринга шаблонов...")
    
    base_url = "http://localhost:8000"
    
    # Тестируем разные страницы
    test_pages = [
        "/cms/",
        "/cms/en/",
        "/cms/ua/",
        "/cms/texts",
        "/cms/en/texts"
    ]
    
    for page in test_pages:
        print(f"\n📋 Страница: {page}")
        
        try:
            response = requests.get(f"{base_url}{page}", timeout=5)
            
            if response.status_code == 200:
                print(f"   ✅ Статус: {response.status_code}")
                print(f"   📊 Размер HTML: {len(response.text)} символов")
                
                # Ищем отладочную информацию
                debug_found = False
                
                # Ищем упоминания "DEBUG INFO"
                if "DEBUG INFO" in response.text:
                    print(f"   ✅ DEBUG INFO найден")
                    debug_found = True
                else:
                    print(f"   ❌ DEBUG INFO не найден")
                
                # Ищем упоминания "lang="
                if "lang=" in response.text:
                    print(f"   ✅ lang= найден")
                    debug_found = True
                else:
                    print(f"   ❌ lang= не найден")
                
                # Ищем упоминания "language_urls="
                if "language_urls=" in response.text:
                    print(f"   ✅ language_urls= найден")
                    debug_found = True
                else:
                    print(f"   ❌ language_urls= не найден")
                
                # Ищем упоминания "supported_languages="
                if "supported_languages=" in response.text:
                    print(f"   ✅ supported_languages= найден")
                    debug_found = True
                else:
                    print(f"   ❌ supported_languages= не найден")
                
                if not debug_found:
                    print(f"   ⚠️  Отладочная информация не найдена")
                    
            else:
                print(f"   ❌ Статус: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

if __name__ == "__main__":
    debug_template_rendering()
