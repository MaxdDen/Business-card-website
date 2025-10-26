#!/usr/bin/env python3
"""
Автотест для проверки динамических изображений и SEO
"""

import sys
import os
import requests
import json
import time

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def log_test(test_name, status, message=""):
    """Логирование результатов теста"""
    status_icon = "✅" if status else "❌"
    print(f"{status_icon} {test_name}")
    if message:
        print(f"    {message}")

def test_dynamic_images_api():
    """Тест API для динамических изображений"""
    try:
        # Тест получения динамических изображений
        response = requests.get('http://localhost:8000/cms/api/dynamic-images', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                log_test("Dynamic Images API - GET", True, f"Найдено {data.get('total_pages', 0)} страниц с изображениями")
                return True
            else:
                log_test("Dynamic Images API - GET", False, f"Ошибка API: {data.get('message', 'Unknown error')}")
                return False
        else:
            log_test("Dynamic Images API - GET", False, f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Dynamic Images API - GET", False, f"Exception: {e}")
        return False

def test_dynamic_images_sync():
    """Тест синхронизации динамических изображений"""
    try:
        # Тест синхронизации динамических изображений
        response = requests.post('http://localhost:8000/cms/api/dynamic-images/sync', 
                               json={}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                results = data.get('results', {})
                log_test("Dynamic Images API - SYNC", True, 
                        f"Синхронизация: {results.get('added_variables', 0)} добавлено, "
                        f"{results.get('skipped_variables', 0)} пропущено")
                return True
            else:
                log_test("Dynamic Images API - SYNC", False, f"Ошибка API: {data.get('message', 'Unknown error')}")
                return False
        else:
            log_test("Dynamic Images API - SYNC", False, f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Dynamic Images API - SYNC", False, f"Exception: {e}")
        return False

def test_dynamic_seo_api():
    """Тест API для динамических SEO"""
    try:
        # Тест получения динамических SEO
        response = requests.get('http://localhost:8000/cms/api/dynamic-seo', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                log_test("Dynamic SEO API - GET", True, f"Найдено {data.get('total_pages', 0)} страниц с SEO")
                return True
            else:
                log_test("Dynamic SEO API - GET", False, f"Ошибка API: {data.get('message', 'Unknown error')}")
                return False
        else:
            log_test("Dynamic SEO API - GET", False, f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Dynamic SEO API - GET", False, f"Exception: {e}")
        return False

def test_dynamic_seo_sync():
    """Тест синхронизации динамических SEO"""
    try:
        # Тест синхронизации динамических SEO
        response = requests.post('http://localhost:8000/cms/api/dynamic-seo/sync', 
                               json={}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                results = data.get('results', {})
                log_test("Dynamic SEO API - SYNC", True, 
                        f"Синхронизация: {results.get('added_variables', 0)} добавлено, "
                        f"{results.get('skipped_variables', 0)} пропущено")
                return True
            else:
                log_test("Dynamic SEO API - SYNC", False, f"Ошибка API: {data.get('message', 'Unknown error')}")
                return False
        else:
            log_test("Dynamic SEO API - SYNC", False, f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Dynamic SEO API - SYNC", False, f"Exception: {e}")
        return False

def test_dynamic_images_ui():
    """Тест UI для динамических изображений"""
    try:
        # Тест загрузки страницы динамических изображений
        response = requests.get('http://localhost:8000/cms/dynamic-images', timeout=10)
        
        if response.status_code == 200:
            content = response.text
            if 'Dynamic Images' in content or 'Динамические изображения' in content:
                log_test("Dynamic Images UI", True, "Страница загружена успешно")
                return True
            else:
                log_test("Dynamic Images UI", False, "Страница не содержит ожидаемого контента")
                return False
        else:
            log_test("Dynamic Images UI", False, f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Dynamic Images UI", False, f"Exception: {e}")
        return False

def test_dynamic_seo_ui():
    """Тест UI для динамических SEO"""
    try:
        # Тест загрузки страницы динамических SEO
        response = requests.get('http://localhost:8000/cms/dynamic-seo', timeout=10)
        
        if response.status_code == 200:
            content = response.text
            if 'Dynamic SEO' in content or 'Динамические SEO' in content:
                log_test("Dynamic SEO UI", True, "Страница загружена успешно")
                return True
            else:
                log_test("Dynamic SEO UI", False, "Страница не содержит ожидаемого контента")
                return False
        else:
            log_test("Dynamic SEO UI", False, f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Dynamic SEO UI", False, f"Exception: {e}")
        return False

def test_template_parser_integration():
    """Тест интеграции с TemplateParser"""
    try:
        from app.utils.template_parser import TemplateParser
        
        parser = TemplateParser()
        
        # Тест парсинга шаблонов
        template_variables = parser.parse_all_templates()
        
        if template_variables:
            log_test("Template Parser Integration", True, f"Найдено {len(template_variables)} страниц с переменными")
            
            # Проверяем наличие переменных изображений и SEO
            has_images = False
            has_seo = False
            
            for page, variables in template_variables.items():
                for variable in variables:
                    if variable.startswith('images.'):
                        has_images = True
                    elif variable.startswith('seo.'):
                        has_seo = True
            
            if has_images:
                log_test("Template Parser - Images Variables", True, "Найдены переменные изображений")
            else:
                log_test("Template Parser - Images Variables", False, "Переменные изображений не найдены")
            
            if has_seo:
                log_test("Template Parser - SEO Variables", True, "Найдены SEO переменные")
            else:
                log_test("Template Parser - SEO Variables", False, "SEO переменные не найдены")
            
            return True
        else:
            log_test("Template Parser Integration", False, "Переменные в шаблонах не найдены")
            return False
            
    except Exception as e:
        log_test("Template Parser Integration", False, f"Exception: {e}")
        return False

def test_database_integration():
    """Тест интеграции с базой данных"""
    try:
        from app.database.db import query_all
        
        # Проверяем наличие переводов для динамических изображений
        dynamic_images_translations = query_all("""
            SELECT COUNT(*) as count FROM texts 
            WHERE page = 'cms_dynamic_images'
        """)
        
        if dynamic_images_translations and dynamic_images_translations[0]['count'] > 0:
            log_test("Database Integration - Dynamic Images Translations", True, 
                    f"Найдено {dynamic_images_translations[0]['count']} переводов")
        else:
            log_test("Database Integration - Dynamic Images Translations", False, "Переводы не найдены")
        
        # Проверяем наличие переводов для динамических SEO
        dynamic_seo_translations = query_all("""
            SELECT COUNT(*) as count FROM texts 
            WHERE page = 'cms_dynamic_seo'
        """)
        
        if dynamic_seo_translations and dynamic_seo_translations[0]['count'] > 0:
            log_test("Database Integration - Dynamic SEO Translations", True, 
                    f"Найдено {dynamic_seo_translations[0]['count']} переводов")
        else:
            log_test("Database Integration - Dynamic SEO Translations", False, "Переводы не найдены")
        
        return True
        
    except Exception as e:
        log_test("Database Integration", False, f"Exception: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование динамических изображений и SEO")
    print("=" * 50)
    
    # Проверяем доступность сервера
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code != 200:
            print("❌ Сервер недоступен. Запустите сервер командой: python start_server.py")
            return False
    except:
        print("❌ Сервер недоступен. Запустите сервер командой: python start_server.py")
        return False
    
    print("✅ Сервер доступен")
    print()
    
    # Запускаем тесты
    tests = [
        test_dynamic_images_api,
        test_dynamic_images_sync,
        test_dynamic_seo_api,
        test_dynamic_seo_sync,
        test_dynamic_images_ui,
        test_dynamic_seo_ui,
        test_template_parser_integration,
        test_database_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} - Exception: {e}")
        print()
    
    print("=" * 50)
    print(f"📊 Результаты: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
        return True
    else:
        print("⚠️  Некоторые тесты не пройдены")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
