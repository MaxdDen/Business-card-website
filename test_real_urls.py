#!/usr/bin/env python3
"""
Простой тест для проверки реального поведения языковых URL
"""

import requests
import sys
import os

def test_real_cms_urls():
    """Тест реальных URL CMS"""
    print("🧪 Тестирование реальных URL CMS...")
    
    base_url = "http://localhost:8000"
    
    # Тестируем переходы между страницами
    test_flows = [
        {
            "name": "Dashboard -> Texts",
            "start": "/cms/",
            "next": "/cms/texts"
        },
        {
            "name": "Dashboard EN -> Texts EN", 
            "start": "/cms/en/",
            "next": "/cms/en/texts"
        },
        {
            "name": "Dashboard UA -> Images UA",
            "start": "/cms/ua/", 
            "next": "/cms/ua/images"
        }
    ]
    
    for flow in test_flows:
        print(f"\n📋 Тест: {flow['name']}")
        print(f"   Начальная страница: {flow['start']}")
        print(f"   Следующая страница: {flow['next']}")
        
        # Проверяем начальную страницу
        start_url = f"{base_url}{flow['start']}"
        try:
            start_response = requests.get(start_url, timeout=5)
            print(f"   ✅ Начальная страница: {start_response.status_code}")
            
            # Ищем языковые ссылки в HTML
            if 'language_urls' in start_response.text:
                print(f"   ✅ Языковые ссылки найдены в HTML")
            else:
                print(f"   ⚠️  Языковые ссылки не найдены в HTML")
                
        except Exception as e:
            print(f"   ❌ Ошибка начальной страницы: {e}")
            continue
            
        # Проверяем следующую страницу
        next_url = f"{base_url}{flow['next']}"
        try:
            next_response = requests.get(next_url, timeout=5)
            print(f"   ✅ Следующая страница: {next_response.status_code}")
            
        except Exception as e:
            print(f"   ❌ Ошибка следующей страницы: {e}")

if __name__ == "__main__":
    test_real_cms_urls()
