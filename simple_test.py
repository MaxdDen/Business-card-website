#!/usr/bin/env python3
"""
Простой тест логики генерации URL
"""

def test_url_generation():
    """Тест генерации URL для CMS"""
    
    # Симулируем логику из middleware
    def generate_cms_urls(current_path, current_language):
        supported_languages = ["en", "ua", "ru"]
        default_language = "en"
        urls = {}
        
        # Убираем существующий языковой префикс, если он есть
        clean_path = current_path
        for lang in supported_languages:
            if current_path.startswith(f'/cms/{lang}/'):
                clean_path = f'/cms/{current_path[len(f"/cms/{lang}"):]}'
                break
            elif current_path == f'/cms/{lang}':
                clean_path = '/cms/'
                break
        
        # Нормализуем путь
        clean_path = clean_path.replace('//', '/')
        
        # Генерируем URL для каждого языка
        for lang in supported_languages:
            if lang == default_language:
                urls[lang] = clean_path
            else:
                if clean_path == '/cms/':
                    urls[lang] = f'/cms/{lang}/'
                else:
                    sub_path = clean_path[4:] if clean_path.startswith('/cms/') else clean_path
                    urls[lang] = f'/cms/{lang}{sub_path}'
        
        return urls
    
    print("🧪 Тест генерации URL для CMS:")
    
    test_cases = [
        ("/cms/ru/texts", "ru"),
        ("/cms/en/images", "en"),
        ("/cms/ua/seo", "ua"),
        ("/cms/texts", "en"),
    ]
    
    for current_path, current_lang in test_cases:
        urls = generate_cms_urls(current_path, current_lang)
        print(f"\nПуть: {current_path} (язык: {current_lang})")
        print(f"URLs: {urls}")
        
        # Проверяем, что URL для текущего языка соответствует текущему пути
        assert urls[current_lang] == current_path, f"URL для {current_lang} должен быть {current_path}"
        
        # Проверяем, что все языки присутствуют
        assert "en" in urls, "Отсутствует английский"
        assert "ru" in urls, "Отсутствует русский"
        assert "ua" in urls, "Отсутствует украинский"
    
    print("\n✅ Все тесты прошли успешно!")

if __name__ == "__main__":
    test_url_generation()
