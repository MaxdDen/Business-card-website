#!/usr/bin/env python3
"""
Детальная отладка переменных шаблонов
"""

import requests
import re
import sys
import os

def debug_template_variables_detailed():
    """Детальная отладка переменных шаблонов"""
    print("🔍 Детальная отладка переменных шаблонов...")
    
    base_url = "http://localhost:8000"
    
    # Тестируем украинскую страницу
    page = "/cms/ua/"
    print(f"\n📋 Страница: {page}")
    
    try:
        response = requests.get(f"{base_url}{page}", timeout=10)
        
        if response.status_code == 200:
            print(f"   ✅ Статус: {response.status_code}")
            print(f"   📊 Размер HTML: {len(response.text)} символов")
            
            # Ищем упоминания переменных
            variables = [
                "lang=",
                "language_urls=",
                "supported_languages=",
                "DEBUG INFO",
                "🚨 DEBUG INFO 🚨",
                "▲ DEBUG INFO ▲"
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
            if all_links:
                print(f"   🔗 Всего ссылок: {len(all_links)}")
                for i, link in enumerate(all_links[:10]):  # Показываем первые 10
                    print(f"     {i+1}. {link}")
            else:
                print(f"   ⚠️  Ссылки не найдены")
                
        else:
            print(f"   ❌ Статус: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

if __name__ == "__main__":
    debug_template_variables_detailed()