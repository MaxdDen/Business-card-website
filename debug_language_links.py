#!/usr/bin/env python3
"""
Отладка языковых ссылок в шаблонах
"""

import requests
import re
import sys
import os

def debug_language_links():
    """Отладка языковых ссылок"""
    print("🔍 Отладка языковых ссылок в шаблонах...")
    
    base_url = "http://localhost:8000"
    
    # Тестируем украинскую страницу
    page = "/cms/ua/"
    print(f"\n📋 Страница: {page}")
    
    try:
        response = requests.get(f"{base_url}{page}", timeout=5)
        
        if response.status_code == 200:
            print(f"   ✅ Статус: {response.status_code}")
            print(f"   📊 Размер HTML: {len(response.text)} символов")
            
            # Ищем языковые ссылки
            lang_links = re.findall(r'href="([^"]*)"[^>]*title="([^"]*)"', response.text)
            if lang_links:
                print(f"   🔗 Найдены языковые ссылки:")
                for href, title in lang_links:
                    if 'cms' in href:
                        print(f"     {href} -> {title}")
            else:
                print(f"   ⚠️  Языковые ссылки не найдены")
            
            # Ищем любые ссылки с языковыми префиксами
            cms_links = re.findall(r'href="(/cms/[^"]*)"', response.text)
            if cms_links:
                print(f"   🔗 Найдены CMS ссылки:")
                for link in cms_links[:10]:  # Показываем первые 10
                    print(f"     {link}")
            else:
                print(f"   ⚠️  CMS ссылки не найдены")
            
            # Ищем упоминания "texts" в ссылках
            texts_links = re.findall(r'href="([^"]*texts[^"]*)"', response.text)
            if texts_links:
                print(f"   🔗 Найдены ссылки на texts:")
                for link in texts_links:
                    print(f"     {link}")
            else:
                print(f"   ⚠️  Ссылки на texts не найдены")
                
        else:
            print(f"   ❌ Статус: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

if __name__ == "__main__":
    debug_language_links()
