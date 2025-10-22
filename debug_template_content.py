#!/usr/bin/env python3
"""
Отладка содержимого шаблонов
"""

import requests
import re
import sys
import os

def debug_template_content():
    """Отладка содержимого шаблонов"""
    print("🔍 Отладка содержимого шаблонов...")
    
    base_url = "http://localhost:8000"
    
    # Тестируем украинскую страницу
    page = "/cms/ua/"
    print(f"\n📋 Страница: {page}")
    
    try:
        response = requests.get(f"{base_url}{page}", timeout=10)
        
        if response.status_code == 200:
            print(f"   ✅ Статус: {response.status_code}")
            print(f"   📊 Размер HTML: {len(response.text)} символов")
            
            # Ищем отладочную информацию
            if "DEBUG INFO" in response.text:
                print(f"   ✅ DEBUG INFO найден")
            else:
                print(f"   ❌ DEBUG INFO не найден")
            
            # Ищем упоминания языков
            lang_mentions = re.findall(r'[^a-zA-Z](en|ru|ua)[^a-zA-Z]', response.text)
            if lang_mentions:
                print(f"   🔍 Упоминания языков: {set(lang_mentions)}")
            else:
                print(f"   ⚠️  Упоминания языков не найдены")
            
            # Ищем любые ссылки
            all_links = re.findall(r'href="([^"]*)"', response.text)
            if all_links:
                print(f"   🔗 Всего ссылок: {len(all_links)}")
                for i, link in enumerate(all_links[:5]):  # Показываем первые 5
                    print(f"     {i+1}. {link}")
            else:
                print(f"   ⚠️  Ссылки не найдены")
                
        else:
            print(f"   ❌ Статус: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

if __name__ == "__main__":
    debug_template_content()
