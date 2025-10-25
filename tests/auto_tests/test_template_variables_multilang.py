#!/usr/bin/env python3
"""
Автотест для проверки мультиязычности страницы Template Variables
"""

import sys
import os
import requests
import time
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_template_variables_multilang():
    """Тест мультиязычности страницы Template Variables"""
    print("🧪 Тестирование мультиязычности Template Variables...")
    
    base_url = "http://localhost:8000"
    
    # Тестируем доступность страницы на разных языках
    languages = ['en', 'ru', 'ua']
    
    for lang in languages:
        print(f"  📝 Тестирование языка: {lang}")
        
        # URL для template-variables с языковым префиксом
        url = f"{base_url}/cms/{lang}/template-variables"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"    ✅ Страница доступна на языке {lang}")
                
                # Проверяем наличие ключевых элементов интерфейса
                content = response.text
                
                # Проверяем заголовок страницы
                if f'<title>{lang.upper()}' in content or 'Template Variables' in content:
                    print(f"    ✅ Заголовок страницы корректен для {lang}")
                else:
                    print(f"    ❌ Проблема с заголовком для {lang}")
                
                # Проверяем наличие переключателя языков
                if 'data-language-button' in content:
                    print(f"    ✅ Переключатель языков присутствует для {lang}")
                else:
                    print(f"    ❌ Переключатель языков отсутствует для {lang}")
                
                # Проверяем наличие кнопок управления
                if 'sync-btn' in content and 'analyze-btn' in content:
                    print(f"    ✅ Кнопки управления присутствуют для {lang}")
                else:
                    print(f"    ❌ Кнопки управления отсутствуют для {lang}")
                
                # Проверяем наличие секций контента
                if 'database_variables' in content or 'template_analysis' in content:
                    print(f"    ✅ Секции контента присутствуют для {lang}")
                else:
                    print(f"    ❌ Секции контента отсутствуют для {lang}")
                    
            else:
                print(f"    ❌ Ошибка доступа к странице {lang}: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"    ❌ Ошибка запроса для {lang}: {e}")
    
    print("  📊 Тестирование API endpoints...")
    
    # Тестируем API endpoints
    api_endpoints = [
        '/cms/api/template-variables',
        '/cms/api/sync-template-variables',
        '/cms/api/template-analysis'
    ]
    
    for endpoint in api_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code in [200, 405]:  # 405 для POST endpoints
                print(f"    ✅ API endpoint {endpoint} доступен")
            else:
                print(f"    ⚠️  API endpoint {endpoint} вернул статус {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"    ❌ Ошибка API endpoint {endpoint}: {e}")
    
    print("  🔍 Проверка переводов в базе данных...")
    
    # Проверяем наличие переводов в базе данных
    try:
        import sqlite3
        db_path = project_root / "data" / "app.db"
        
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Проверяем наличие переводов для template_variables
            cursor.execute("""
                SELECT COUNT(*) FROM texts 
                WHERE page = 'cms_template_variables' 
                AND lang IN ('en', 'ru', 'ua')
            """)
            
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"    ✅ Найдено {count} переводов для template_variables")
                
                # Проверяем конкретные ключи
                required_keys = ['title', 'subtitle', 'sync_variables', 'analyze_templates']
                
                for key in required_keys:
                    cursor.execute("""
                        SELECT COUNT(*) FROM texts 
                        WHERE page = 'cms_template_variables' 
                        AND key = ? AND lang IN ('en', 'ru', 'ua')
                    """, (key,))
                    
                    key_count = cursor.fetchone()[0]
                    if key_count >= 3:  # Должно быть для всех языков
                        print(f"    ✅ Ключ '{key}' переведен на все языки")
                    else:
                        print(f"    ❌ Ключ '{key}' переведен не на все языки")
            else:
                print("    ❌ Переводы для template_variables не найдены")
            
            conn.close()
        else:
            print("    ❌ База данных не найдена")
            
    except Exception as e:
        print(f"    ❌ Ошибка проверки базы данных: {e}")
    
    print("✅ Тестирование мультиязычности Template Variables завершено")

if __name__ == "__main__":
    test_template_variables_multilang()
