#!/usr/bin/env python3
"""
Детальная отладка HTML содержимого
"""

import requests
import re
import sys
import os

def debug_html_content():
    """Детальная отладка HTML"""
    print("🔍 Детальная отладка HTML содержимого...")
    
    base_url = "http://localhost:8000"
    
    # Тестируем главную страницу CMS
    page = "/cms/ua/"
    print(f"\n📋 Страница: {page}")
    
    try:
        response = requests.get(f"{base_url}{page}", timeout=5)
        
        if response.status_code == 200:
            print(f"   ✅ Статус: {response.status_code}")
            print(f"   📊 Размер HTML: {len(response.text)} символов")
            
            # Ищем отладочную информацию
            debug_patterns = [
                r'Debug:.*?lang=([^<]+)',
                r'language_urls=([^<]+)',
                r'supported_languages=([^<]+)',
                r'URLs:.*?en: ([^<]+)',
                r'URLs:.*?ru: ([^<]+)',
                r'URLs:.*?ua: ([^<]+)'
            ]
            
            print(f"   🔍 Поиск отладочной информации:")
            for i, pattern in enumerate(debug_patterns):
                matches = re.findall(pattern, response.text, re.DOTALL)
                if matches:
                    print(f"     ✅ Паттерн {i+1}: {matches}")
                else:
                    print(f"     ❌ Паттерн {i+1}: не найден")
            
            # Ищем любые упоминания языков
            lang_mentions = re.findall(r'[^a-zA-Z](en|ru|ua)[^a-zA-Z]', response.text)
            if lang_mentions:
                print(f"   🔍 Упоминания языков: {set(lang_mentions)}")
            else:
                print(f"   ⚠️  Упоминания языков не найдены")
            
            # Ищем любые ссылки
            all_links = re.findall(r'href="([^"]*)"', response.text)
            cms_links = [link for link in all_links if '/cms' in link]
            if cms_links:
                print(f"   🔗 CMS ссылки найдены:")
                for link in cms_links[:10]:  # Показываем первые 10
                    print(f"     {link}")
            else:
                print(f"   ⚠️  CMS ссылки не найдены")
            
            # Ищем любые упоминания "Debug"
            debug_mentions = re.findall(r'Debug', response.text)
            if debug_mentions:
                print(f"   🔍 Упоминания 'Debug': {len(debug_mentions)}")
            else:
                print(f"   ⚠️  Упоминания 'Debug' не найдены")
                
        else:
            print(f"   ❌ Статус: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

if __name__ == "__main__":
    debug_html_content()
