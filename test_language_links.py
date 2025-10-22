#!/usr/bin/env python3
"""
Тест языковых ссылок в шаблонах
"""

import requests
import re
import sys
import os

def test_language_links():
    """Тест языковых ссылок"""
    print("🧪 Тест языковых ссылок в шаблонах...")
    
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
                
                # Ищем отладочную информацию
                debug_match = re.search(r'Debug:.*?lang=([^<]+).*?urls=([^<]+)', response.text, re.DOTALL)
                if debug_match:
                    lang = debug_match.group(1).strip()
                    urls = debug_match.group(2).strip()
                    print(f"   🔍 Debug info найдена:")
                    print(f"     lang: {lang}")
                    print(f"     urls: {urls}")
                else:
                    print(f"   ⚠️  Debug info не найдена")
                
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
                    for link in cms_links[:5]:  # Показываем первые 5
                        print(f"     {link}")
                else:
                    print(f"   ⚠️  CMS ссылки не найдены")
                    
            else:
                print(f"   ❌ Статус: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

if __name__ == "__main__":
    test_language_links()
