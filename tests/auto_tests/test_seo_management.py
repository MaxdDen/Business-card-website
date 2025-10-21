#!/usr/bin/env python3
"""
Автотест для SEO функциональности CMS
Проверяет API endpoints для работы с SEO данными
"""

import requests
import json
import sys
import os
from datetime import datetime

# Добавляем путь к корню проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Конфигурация
BASE_URL = "http://localhost:8000"
CMS_BASE_URL = f"{BASE_URL}/cms"

# Тестовые данные
TEST_SEO_DATA = {
    "home_ru": {
        "title": "Главная страница - Дистрибьютор электроники",
        "description": "Официальный дистрибьютор электронной продукции. Качественные товары по доступным ценам.",
        "keywords": "электроника, дистрибьютор, товары, качество"
    },
    "about_en": {
        "title": "About Us - Electronics Distributor",
        "description": "Official distributor of electronic products. Quality goods at affordable prices.",
        "keywords": "electronics, distributor, products, quality"
    },
    "catalog_ua": {
        "title": "Каталог - Дистриб'ютор електроніки",
        "description": "Офіційний дистриб'ютор електронної продукції. Якісні товари за доступними цінами.",
        "keywords": "електроніка, дистриб'ютор, товари, якість"
    }
}

def log_test(test_name, status, message=""):
    """Логирование результатов теста"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_icon = "✅" if status == "PASS" else "❌"
    print(f"[{timestamp}] {status_icon} {test_name}: {status}")
    if message:
        print(f"    {message}")

def test_seo_api_get():
    """Тест получения SEO данных"""
    test_name = "SEO API GET"
    
    try:
        # Тестируем получение данных для разных страниц и языков
        for page_lang, seo_data in TEST_SEO_DATA.items():
            page, lang = page_lang.split('_')
            
            response = requests.get(f"{CMS_BASE_URL}/api/seo", params={
                "page": page,
                "lang": lang
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    log_test(f"{test_name} - {page_lang}", "PASS", f"Получены данные: {data.get('seo', {})}")
                else:
                    log_test(f"{test_name} - {page_lang}", "FAIL", f"API вернул ошибку: {data.get('message')}")
                    return False
            else:
                log_test(f"{test_name} - {page_lang}", "FAIL", f"HTTP {response.status_code}")
                return False
                
        return True
        
    except Exception as e:
        log_test(test_name, "FAIL", f"Исключение: {str(e)}")
        return False

def test_seo_api_save():
    """Тест сохранения SEO данных"""
    test_name = "SEO API SAVE"
    
    try:
        # Тестируем сохранение данных для каждой комбинации
        for page_lang, seo_data in TEST_SEO_DATA.items():
            page, lang = page_lang.split('_')
            
            payload = {
                "page": page,
                "lang": lang,
                "seo": seo_data
            }
            
            response = requests.post(
                f"{CMS_BASE_URL}/api/seo",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    log_test(f"{test_name} - {page_lang}", "PASS", f"Данные сохранены: {data.get('message')}")
                else:
                    log_test(f"{test_name} - {page_lang}", "FAIL", f"Ошибка сохранения: {data.get('message')}")
                    return False
            else:
                log_test(f"{test_name} - {page_lang}", "FAIL", f"HTTP {response.status_code}")
                return False
                
        return True
        
    except Exception as e:
        log_test(test_name, "FAIL", f"Исключение: {str(e)}")
        return False

def test_seo_validation():
    """Тест валидации SEO данных"""
    test_name = "SEO VALIDATION"
    
    try:
        # Тест слишком длинного title
        long_title = "A" * 61  # Превышает лимит в 60 символов
        payload = {
            "page": "home",
            "lang": "ru",
            "seo": {
                "title": long_title,
                "description": "Test description",
                "keywords": "test, keywords"
            }
        }
        
        response = requests.post(
            f"{CMS_BASE_URL}/api/seo",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if not data.get("success") and "превышать 60 символов" in data.get("message", ""):
                log_test(f"{test_name} - Title length", "PASS", "Валидация длины title работает")
            else:
                log_test(f"{test_name} - Title length", "FAIL", "Валидация длины title не работает")
                return False
        else:
            log_test(f"{test_name} - Title length", "FAIL", f"HTTP {response.status_code}")
            return False
        
        # Тест слишком длинного description
        long_description = "A" * 161  # Превышает лимит в 160 символов
        payload = {
            "page": "home",
            "lang": "ru",
            "seo": {
                "title": "Valid title",
                "description": long_description,
                "keywords": "test, keywords"
            }
        }
        
        response = requests.post(
            f"{CMS_BASE_URL}/api/seo",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if not data.get("success") and "превышать 160 символов" in data.get("message", ""):
                log_test(f"{test_name} - Description length", "PASS", "Валидация длины description работает")
            else:
                log_test(f"{test_name} - Description length", "FAIL", "Валидация длины description не работает")
                return False
        else:
            log_test(f"{test_name} - Description length", "FAIL", f"HTTP {response.status_code}")
            return False
        
        # Тест слишком длинных keywords
        long_keywords = "A" * 256  # Превышает лимит в 255 символов
        payload = {
            "page": "home",
            "lang": "ru",
            "seo": {
                "title": "Valid title",
                "description": "Valid description",
                "keywords": long_keywords
            }
        }
        
        response = requests.post(
            f"{CMS_BASE_URL}/api/seo",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if not data.get("success") and "превышать 255 символов" in data.get("message", ""):
                log_test(f"{test_name} - Keywords length", "PASS", "Валидация длины keywords работает")
            else:
                log_test(f"{test_name} - Keywords length", "FAIL", "Валидация длины keywords не работает")
                return False
        else:
            log_test(f"{test_name} - Keywords length", "FAIL", f"HTTP {response.status_code}")
            return False
            
        return True
        
    except Exception as e:
        log_test(test_name, "FAIL", f"Исключение: {str(e)}")
        return False

def test_seo_invalid_params():
    """Тест недопустимых параметров"""
    test_name = "SEO INVALID PARAMS"
    
    try:
        # Тест недопустимой страницы
        response = requests.get(f"{CMS_BASE_URL}/api/seo", params={
            "page": "invalid_page",
            "lang": "ru"
        })
        
        if response.status_code == 200:
            data = response.json()
            if not data.get("success") and "Недопустимая страница" in data.get("message", ""):
                log_test(f"{test_name} - Invalid page", "PASS", "Валидация страницы работает")
            else:
                log_test(f"{test_name} - Invalid page", "FAIL", "Валидация страницы не работает")
                return False
        else:
            log_test(f"{test_name} - Invalid page", "FAIL", f"HTTP {response.status_code}")
            return False
        
        # Тест недопустимого языка
        response = requests.get(f"{CMS_BASE_URL}/api/seo", params={
            "page": "home",
            "lang": "invalid_lang"
        })
        
        if response.status_code == 200:
            data = response.json()
            if not data.get("success") and "Недопустимый язык" in data.get("message", ""):
                log_test(f"{test_name} - Invalid language", "PASS", "Валидация языка работает")
            else:
                log_test(f"{test_name} - Invalid language", "FAIL", "Валидация языка не работает")
                return False
        else:
            log_test(f"{test_name} - Invalid language", "FAIL", f"HTTP {response.status_code}")
            return False
            
        return True
        
    except Exception as e:
        log_test(test_name, "FAIL", f"Исключение: {str(e)}")
        return False

def test_seo_roundtrip():
    """Тест полного цикла: сохранение -> получение"""
    test_name = "SEO ROUNDTRIP"
    
    try:
        # Сохраняем данные
        test_data = {
            "title": "Test Title",
            "description": "Test Description",
            "keywords": "test, keywords"
        }
        
        payload = {
            "page": "home",
            "lang": "ru",
            "seo": test_data
        }
        
        # Сохраняем
        save_response = requests.post(
            f"{CMS_BASE_URL}/api/seo",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if save_response.status_code != 200:
            log_test(test_name, "FAIL", f"Ошибка сохранения: HTTP {save_response.status_code}")
            return False
        
        save_data = save_response.json()
        if not save_data.get("success"):
            log_test(test_name, "FAIL", f"Ошибка сохранения: {save_data.get('message')}")
            return False
        
        # Получаем данные
        get_response = requests.get(f"{CMS_BASE_URL}/api/seo", params={
            "page": "home",
            "lang": "ru"
        })
        
        if get_response.status_code != 200:
            log_test(test_name, "FAIL", f"Ошибка получения: HTTP {get_response.status_code}")
            return False
        
        get_data = get_response.json()
        if not get_data.get("success"):
            log_test(test_name, "FAIL", f"Ошибка получения: {get_data.get('message')}")
            return False
        
        # Проверяем, что данные совпадают
        retrieved_seo = get_data.get("seo", {})
        if (retrieved_seo.get("title") == test_data["title"] and
            retrieved_seo.get("description") == test_data["description"] and
            retrieved_seo.get("keywords") == test_data["keywords"]):
            log_test(test_name, "PASS", "Данные корректно сохранены и получены")
            return True
        else:
            log_test(test_name, "FAIL", f"Данные не совпадают. Ожидалось: {test_data}, Получено: {retrieved_seo}")
            return False
            
    except Exception as e:
        log_test(test_name, "FAIL", f"Исключение: {str(e)}")
        return False

def main():
    """Запуск всех тестов"""
    print("=" * 60)
    print("🧪 АВТОТЕСТ SEO ФУНКЦИОНАЛЬНОСТИ CMS")
    print("=" * 60)
    print(f"Тестируем API: {CMS_BASE_URL}")
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Получение SEO данных", test_seo_api_get),
        ("Сохранение SEO данных", test_seo_api_save),
        ("Валидация SEO данных", test_seo_validation),
        ("Недопустимые параметры", test_seo_invalid_params),
        ("Полный цикл (сохранение->получение)", test_seo_roundtrip)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"🔍 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - ПРОЙДЕН")
            else:
                print(f"❌ {test_name} - ПРОВАЛЕН")
        except Exception as e:
            print(f"❌ {test_name} - ОШИБКА: {str(e)}")
        
        print()
    
    print("=" * 60)
    print(f"📊 РЕЗУЛЬТАТЫ: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        return True
    else:
        print("⚠️  НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
