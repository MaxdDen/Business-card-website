#!/usr/bin/env python3
"""
Отладка переменных шаблонов
"""

import requests
import re
import sys
import os

def debug_template_variables():
    """Отладка переменных шаблонов"""
    print("🔍 Отладка переменных шаблонов...")
    
    base_url = "http://localhost:8000"
    
    # Тестируем главную страницу CMS
    page = "/cms/ua/"
    print(f"\n📋 Страница: {page}")
    
    try:
        response = requests.get(f"{base_url}{page}", timeout=5)
        
        if response.status_code == 200:
            print(f"   ✅ Статус: {response.status_code}")
            print(f"   📊 Размер HTML: {len(response.text)} символов")
            
            # Ищем упоминания переменных
            variables = [
                "lang=",
                "language_urls=",
                "supported_languages=",
                "DEBUG INFO",
                "🚨 DEBUG INFO 🚨"
            ]
            
            print(f"   🔍 Поиск переменных:")
            for var in variables:
                if var in response.text:
                    print(f"     ✅ {var} найден")
                else:
                    print(f"     ❌ {var} не найден")
            
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
                
        else:
            print(f"   ❌ Статус: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

if __name__ == "__main__":
    debug_template_variables()