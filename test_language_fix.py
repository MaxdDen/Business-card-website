#!/usr/bin/env python3
"""
Простой тест для проверки исправления сохранения языка
"""

import sys
import os

# Добавляем корневую директорию проекта в путь
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.site.middleware import LanguageMiddleware

def test_language_extraction():
    """Тест извлечения языка"""
    middleware = LanguageMiddleware(None)
    
    print("🧪 Тест извлечения языка из URL:")
    
    test_cases = [
        ("/cms/ru/texts", "ru"),
        ("/cms/en/images", "en"),
        ("/cms/ua/seo", "ua"),
        ("/cms/texts", "en"),  # по умолчанию
        ("/cms/", "en"),        # по умолчанию
    ]
    
    for url, expected in test_cases:
        result = middleware.extract_language_from_url(url)
        status = "✅" if result == expected else "❌"
        print(f"{status} {url} -> {result} (ожидалось: {expected})")
        assert result == expected

def test_url_generation():
    """Тест генерации URL"""
    middleware = LanguageMiddleware(None)
    
    print("\n🧪 Тест генерации URL для переключателя языков:")
    
    test_cases = [
        ("/cms/ru/texts", "ru"),
        ("/cms/en/images", "en"),
        ("/cms/ua/seo", "ua"),
    ]
    
    for current_path, current_lang in test_cases:
        urls = middleware.get_language_urls(current_path, current_lang)
        print(f"\nТекущий путь: {current_path} (язык: {current_lang})")
        print(f"Сгенерированные URL: {urls}")
        
        # Проверяем, что URL для текущего языка соответствует текущему пути
        assert urls[current_lang] == current_path, f"URL для {current_lang} должен быть {current_path}, получен {urls[current_lang]}"
        
        # Проверяем, что все языки присутствуют
        assert "en" in urls, "Отсутствует URL для английского"
        assert "ru" in urls, "Отсутствует URL для русского"
        assert "ua" in urls, "Отсутствует URL для украинского"

if __name__ == "__main__":
    print("🔧 Тестирование исправления сохранения языка")
    print("=" * 50)
    
    try:
        test_language_extraction()
        print("\n✅ Тест извлечения языка прошел успешно")
        
        test_url_generation()
        print("\n✅ Тест генерации URL прошел успешно")
        
        print("\n🎉 Все тесты прошли! Язык должен сохраняться при переходах.")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)
