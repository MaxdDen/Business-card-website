#!/usr/bin/env python3
"""
Отладка статуса сервера
"""

import requests
import sys
import os

def debug_server_status():
    """Отладка статуса сервера"""
    print("🔍 Отладка статуса сервера...")
    
    base_url = "http://localhost:8000"
    
    # Тестируем разные страницы
    test_pages = [
        "/",
        "/cms/",
        "/cms/ua/",
        "/cms/texts"
    ]
    
    for page in test_pages:
        print(f"\n📋 Страница: {page}")
        
        try:
            response = requests.get(f"{base_url}{page}", timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ Статус: {response.status_code}")
                print(f"   📊 Размер HTML: {len(response.text)} символов")
                
                # Ищем языковые ссылки
                if 'href=' in response.text:
                    print(f"   ✅ Ссылки найдены")
                else:
                    print(f"   ⚠️  Ссылки не найдены")
                    
            else:
                print(f"   ❌ Статус: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Таймаут (сервер не отвечает)")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Ошибка подключения (сервер не запущен)")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

if __name__ == "__main__":
    debug_server_status()
