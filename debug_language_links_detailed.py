#!/usr/bin/env python3
"""
Детальная отладка языковых ссылок
"""

import requests
import re
import sys
import os

def debug_language_links_detailed():
    """Детальная отладка языковых ссылок"""
    print("🔍 Детальная отладка языковых ссылок...")
    
    base_url = "http://localhost:8000"
    
    # Тестируем украинскую страницу
    page = "/cms/ua/"
    print(f"\n📋 Страница: {page}")
    
    try:
        response = requests.get(f"{base_url}{page}", timeout=10)
        
        if response.status_code == 200:
            print(f"   ✅ Статус: {response.status_code}")
            print(f"   📊 Размер HTML: {len(response.text)} символов")
            
            # Ищем все ссылки
            all_links = re.findall(r'href="([^"]*)"', response.text)
            cms_links = [link for link in all_links if '/cms' in link]
            
            print(f"   🔗 Всего CMS ссылок: {len(cms_links)}")
            for i, link in enumerate(cms_links[:10]):  # Показываем первые 10
                print(f"     {i+1}. {link}")
            
            # Ищем ссылки на texts
            texts_links = [link for link in cms_links if 'texts' in link]
            if texts_links:
                print(f"   🔗 Ссылки на texts:")
                for link in texts_links:
                    print(f"     {link}")
            else:
                print(f"   ⚠️  Ссылки на texts не найдены")
            
            # Ищем языковые ссылки с title
            lang_links = re.findall(r'href="([^"]*)"[^>]*title="([^"]*)"', response.text)
            if lang_links:
                print(f"   🔗 Языковые ссылки с title:")
                for href, title in lang_links:
                    if 'cms' in href:
                        print(f"     {href} -> {title}")
            else:
                print(f"   ⚠️  Языковые ссылки с title не найдены")
                
        else:
            print(f"   ❌ Статус: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

if __name__ == "__main__":
    debug_language_links_detailed()
