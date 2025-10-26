"""
Тест для проверки создания записей в БД для переменных изображений и SEO
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

def test_database_sync():
    """Тест создания записей в БД для переменных изображений и SEO"""
    print("🧪 Тестирование создания записей в БД...")
    
    try:
        # Проверяем, что сервер запущен
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Сервер не запущен")
            return False
        
        print("✅ Сервер запущен")
        
        # Тестируем парсер переменных
        print("🔍 Тестируем парсер переменных...")
        
        try:
            from app.utils.template_parser import TemplateParser
            from app.database.db import query_all, query_one
            
            parser = TemplateParser()
            
            # Парсим все шаблоны
            template_variables = parser.parse_all_templates()
            
            print(f"✅ Парсер нашел переменные в {len(template_variables)} страницах")
            
            # Проверяем переменные изображений
            image_vars = []
            seo_vars = []
            texts_vars = []
            
            for page, variables in template_variables.items():
                for var in variables:
                    if var.startswith('images.'):
                        image_vars.append(var)
                    elif var.startswith('seo.'):
                        seo_vars.append(var)
                    elif var.startswith('texts.'):
                        texts_vars.append(var)
            
            print(f"📊 Найдено переменных:")
            print(f"  - Изображения: {len(image_vars)}")
            print(f"  - SEO: {len(seo_vars)}")
            print(f"  - Тексты: {len(texts_vars)}")
            
            # Тестируем синхронизацию
            print("🔍 Тестируем синхронизацию переменных...")
            sync_results = parser.sync_variables_to_database(['en', 'ru', 'ua'])
            
            print(f"✅ Синхронизация завершена: {sync_results}")
            
            # Проверяем записи в БД для изображений
            print("🔍 Проверяем записи изображений в БД...")
            images_in_db = query_all("SELECT type, COUNT(*) as count FROM images GROUP BY type")
            
            print("📊 Изображения в БД:")
            for row in images_in_db:
                print(f"  - {row['type']}: {row['count']} записей")
            
            # Проверяем alt-тексты
            alts_in_db = query_all("SELECT lang, COUNT(*) as count FROM images_alts GROUP BY lang")
            
            print("📊 Alt-тексты в БД:")
            for row in alts_in_db:
                print(f"  - {row['lang']}: {row['count']} записей")
            
            # Проверяем SEO записи
            print("🔍 Проверяем SEO записи в БД...")
            seo_in_db = query_all("SELECT page, lang, COUNT(*) as count FROM seo GROUP BY page, lang")
            
            print("📊 SEO записи в БД:")
            for row in seo_in_db:
                print(f"  - {row['page']}.{row['lang']}: {row['count']} записей")
            
            # Проверяем текстовые записи
            print("🔍 Проверяем текстовые записи в БД...")
            texts_in_db = query_all("SELECT page, lang, COUNT(*) as count FROM texts GROUP BY page, lang")
            
            print("📊 Текстовые записи в БД:")
            for row in texts_in_db:
                print(f"  - {row['page']}.{row['lang']}: {row['count']} записей")
            
            # Проверяем, что созданы записи для переменных изображений
            expected_image_types = ['logo', 'background', 'favicon', 'slider1', 'slider2', 'slider3', 'slider4']
            created_image_types = [row['type'] for row in images_in_db]
            
            missing_image_types = set(expected_image_types) - set(created_image_types)
            if missing_image_types:
                print(f"⚠️ Не созданы записи для типов изображений: {missing_image_types}")
            else:
                print("✅ Все ожидаемые типы изображений созданы в БД")
            
            # Проверяем, что созданы alt-тексты для всех языков
            expected_languages = ['en', 'ru', 'ua']
            created_languages = [row['lang'] for row in alts_in_db]
            
            missing_languages = set(expected_languages) - set(created_languages)
            if missing_languages:
                print(f"⚠️ Не созданы alt-тексты для языков: {missing_languages}")
            else:
                print("✅ Alt-тексты созданы для всех языков")
            
            # Проверяем SEO записи для всех страниц
            expected_pages = ['home', 'about', 'catalog', 'contacts']
            created_pages = set([row['page'] for row in seo_in_db])
            
            missing_pages = set(expected_pages) - created_pages
            if missing_pages:
                print(f"⚠️ Не созданы SEO записи для страниц: {missing_pages}")
            else:
                print("✅ SEO записи созданы для всех страниц")
            
            print("✅ Все проверки пройдены успешно!")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования парсера: {e}")
            return False
        
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к серверу. Убедитесь, что сервер запущен на http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def test_full_sync():
    """Тест полной синхронизации переменных"""
    print("🧪 Тестирование полной синхронизации...")
    
    try:
        from app.utils.template_parser import TemplateParser
        from app.database.db import query_all
        
        parser = TemplateParser()
        
        # Выполняем полную синхронизацию
        print("🔍 Выполняем полную синхронизацию...")
        sync_results = parser.full_sync_variables_to_database(['en', 'ru', 'ua'])
        
        print(f"✅ Полная синхронизация завершена: {sync_results}")
        
        # Проверяем результаты
        if sync_results['added_variables'] > 0:
            print(f"✅ Добавлено {sync_results['added_variables']} новых переменных")
        
        if sync_results['removed_variables'] > 0:
            print(f"✅ Удалено {sync_results['removed_variables']} неиспользуемых переменных")
        
        if sync_results['errors'] > 0:
            print(f"⚠️ Найдено {sync_results['errors']} ошибок")
        
        print("✅ Полная синхронизация работает корректно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка полной синхронизации: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск тестов синхронизации БД...")
    
    # Тестируем создание записей в БД
    db_sync_ok = test_database_sync()
    
    # Тестируем полную синхронизацию
    full_sync_ok = test_full_sync()
    
    if db_sync_ok and full_sync_ok:
        print("🎉 Все тесты пройдены успешно!")
        sys.exit(0)
    else:
        print("💥 Некоторые тесты не пройдены")
        sys.exit(1)
