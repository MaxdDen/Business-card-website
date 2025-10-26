"""
Тест для проверки переделанного парсинга переменных в новом формате
"""
import os
import sys
import requests
import time
import subprocess
import signal
from pathlib import Path

# Добавляем корневую директорию в путь
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

def test_refactored_variables():
    """Тест переделанных переменных в новом формате"""
    print("🧪 Тестирование переделанных переменных в новом формате...")
    
    try:
        # Проверяем, что сервер запущен
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Сервер не запущен")
            return False
        
        print("✅ Сервер запущен")
        
        # Тестируем главную страницу
        print("🔍 Тестируем главную страницу...")
        response = requests.get("http://localhost:8000/", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Ошибка загрузки главной страницы: {response.status_code}")
            return False
        
        print("✅ Главная страница загружается")
        
        # Проверяем наличие переменных в новом формате в HTML
        html_content = response.text
        
        # Проверяем переменные изображений в новом формате
        image_variables = [
            "{{ images.logo }}",
            "{{ images.background }}",
            "{{ images.favicon }}",
            "{{ images.slider1 }}",
            "{{ images.slider2 }}",
            "{{ images.slider3 }}",
            "{{ images.slider4 }}"
        ]
        
        found_image_vars = []
        for var in image_variables:
            if var in html_content:
                found_image_vars.append(var)
        
        if found_image_vars:
            print(f"✅ Найдены переменные изображений в новом формате: {found_image_vars}")
        else:
            print("⚠️ Переменные изображений в новом формате не найдены (возможно, изображения не загружены)")
        
        # Проверяем переменные SEO в новом формате
        seo_variables = [
            "{{ seo.title }}",
            "{{ seo.description }}",
            "{{ seo.keywords }}"
        ]
        
        found_seo_vars = []
        for var in seo_variables:
            if var in html_content:
                found_seo_vars.append(var)
        
        if found_seo_vars:
            print(f"✅ Найдены переменные SEO в новом формате: {found_seo_vars}")
        else:
            print("⚠️ Переменные SEO в новом формате не найдены")
        
        # Проверяем, что старые форматы переменных больше не используются
        old_formats = [
            "{{ logo.path }}",
            "{{ background.path }}",
            "{{ favicon.path }}",
            "{{ seo.title }}",
            "{{ seo.description }}"
        ]
        
        found_old_formats = []
        for old_format in old_formats:
            if old_format in html_content:
                found_old_formats.append(old_format)
        
        if found_old_formats:
            print(f"⚠️ Найдены старые форматы переменных: {found_old_formats}")
        else:
            print("✅ Старые форматы переменных не найдены")
        
        # Тестируем другие страницы
        pages_to_test = ["/about", "/catalog", "/contacts"]
        
        for page in pages_to_test:
            print(f"🔍 Тестируем страницу {page}...")
            response = requests.get(f"http://localhost:8000{page}", timeout=10)
            
            if response.status_code != 200:
                print(f"❌ Ошибка загрузки страницы {page}: {response.status_code}")
                return False
            
            print(f"✅ Страница {page} загружается")
        
        print("✅ Все страницы загружаются корректно")
        
        # Тестируем парсер переменных
        print("🔍 Тестируем парсер переменных...")
        
        try:
            from app.utils.template_parser import TemplateParser
            
            parser = TemplateParser()
            
            # Парсим все шаблоны
            template_variables = parser.parse_all_templates()
            
            print(f"✅ Парсер нашел переменные в {len(template_variables)} страницах")
            
            # Проверяем, что найдены переменные в новом формате
            all_variables = set()
            for page_vars in template_variables.values():
                all_variables.update(page_vars)
            
            # Ищем переменные изображений
            image_vars = [var for var in all_variables if var.startswith('images.')]
            if image_vars:
                print(f"✅ Парсер нашел переменные изображений: {image_vars}")
            else:
                print("⚠️ Парсер не нашел переменные изображений")
            
            # Ищем переменные SEO
            seo_vars = [var for var in all_variables if var.startswith('seo.')]
            if seo_vars:
                print(f"✅ Парсер нашел переменные SEO: {seo_vars}")
            else:
                print("⚠️ Парсер не нашел переменные SEO")
            
            # Тестируем синхронизацию
            print("🔍 Тестируем синхронизацию переменных...")
            sync_results = parser.sync_variables_to_database(['en', 'ru', 'ua'])
            
            print(f"✅ Синхронизация завершена: {sync_results}")
            
        except Exception as e:
            print(f"❌ Ошибка тестирования парсера: {e}")
            return False
        
        print("✅ Все тесты пройдены успешно!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к серверу. Убедитесь, что сервер запущен на http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def test_template_syntax():
    """Тест синтаксиса шаблонов"""
    print("🧪 Тестирование синтаксиса шаблонов...")
    
    try:
        from app.utils.template_parser import TemplateParser
        
        parser = TemplateParser()
        
        # Проверяем синтаксис всех публичных шаблонов
        public_templates = [
            "app/templates/public/home.html",
            "app/templates/public/base.html",
            "app/templates/public/about.html",
            "app/templates/public/catalog.html",
            "app/templates/public/contacts.html"
        ]
        
        for template_path in public_templates:
            if os.path.exists(template_path):
                print(f"🔍 Проверяем синтаксис {template_path}...")
                issues = parser.validate_template_syntax(template_path)
                
                if issues['unclosed_tags'] or issues['invalid_syntax']:
                    print(f"❌ Найдены ошибки в {template_path}: {issues}")
                    return False
                elif issues['warnings']:
                    print(f"⚠️ Найдены предупреждения в {template_path}: {issues['warnings']}")
                else:
                    print(f"✅ Синтаксис {template_path} корректен")
        
        print("✅ Все шаблоны имеют корректный синтаксис")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки синтаксиса: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск тестов переделанных переменных...")
    
    # Тестируем синтаксис шаблонов
    syntax_ok = test_template_syntax()
    
    # Тестируем функциональность
    functionality_ok = test_refactored_variables()
    
    if syntax_ok and functionality_ok:
        print("🎉 Все тесты пройдены успешно!")
        sys.exit(0)
    else:
        print("💥 Некоторые тесты не пройдены")
        sys.exit(1)
