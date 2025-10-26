#!/usr/bin/env python3
"""
Тест системы alt-текстов для изображений
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.database.db import query_one, query_all, execute
from app.site.routes import get_image_with_alt, get_slider_images_with_alt, get_all_images_for_template
from app.cms.routes import get_all_images_for_template as get_cms_images_for_template


def test_database_schema():
    """Тест структуры базы данных"""
    print("🔍 Тестирование структуры базы данных...")
    
    try:
        # Проверяем существование таблицы images_alts
        result = query_one("SELECT name FROM sqlite_master WHERE type='table' AND name='images_alts'")
        assert result is not None, "Таблица images_alts не найдена"
        print("✅ Таблица images_alts существует")
        
        # Проверяем структуру таблицы
        result = query_all("PRAGMA table_info(images_alts)")
        columns = [col['name'] for col in result]
        
        expected_columns = ['id', 'image_id', 'lang', 'alt_text', 'created_at']
        for col in expected_columns:
            assert col in columns, f"Колонка {col} не найдена в таблице images_alts"
        print("✅ Структура таблицы images_alts корректна")
        
        # Проверяем индексы
        result = query_all("PRAGMA index_list(images_alts)")
        index_names = [idx['name'] for idx in result]
        assert 'idx_images_alts_image_id' in index_names, "Индекс по image_id не найден"
        assert 'idx_images_alts_lang' in index_names, "Индекс по lang не найден"
        print("✅ Индексы таблицы images_alts созданы")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования структуры БД: {e}")
        return False


def test_image_functions():
    """Тест функций работы с изображениями"""
    print("🔍 Тестирование функций работы с изображениями...")
    
    try:
        # Тестируем get_image_with_alt
        logo = get_image_with_alt("logo", "ru")
        print(f"✅ get_image_with_alt работает: {logo}")
        
        # Тестируем get_slider_images_with_alt
        slider_images = get_slider_images_with_alt("ru")
        print(f"✅ get_slider_images_with_alt работает: {len(slider_images)} изображений")
        
        # Тестируем get_all_images_for_template
        images = get_all_images_for_template("ru")
        print(f"✅ get_all_images_for_template работает: {len(images)} переменных")
        
        # Проверяем структуру возвращаемых данных
        expected_keys = ['logo', 'logo_alt', 'background', 'background_alt', 'favicon', 'favicon_alt']
        for i in range(1, 5):
            expected_keys.extend([f'slider{i}', f'slider{i}_alt'])
        
        for key in expected_keys:
            assert key in images, f"Ключ {key} не найден в переменных изображений"
        print("✅ Структура переменных изображений корректна")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования функций: {e}")
        return False


def test_alt_text_crud():
    """Тест CRUD операций с alt-текстами"""
    print("🔍 Тестирование CRUD операций с alt-текстами...")
    
    try:
        # Создаем тестовое изображение
        execute("""
            INSERT INTO images (name, path, original_path, type, "order") 
            VALUES (?, ?, ?, ?, ?)
        """, ("test_image.jpg", "test.jpg", "test_orig.jpg", "logo", 0))
        
        # Получаем ID созданного изображения
        image = query_one("SELECT id FROM images WHERE name = 'test_image.jpg'")
        image_id = image['id']
        print(f"✅ Создано тестовое изображение с ID: {image_id}")
        
        # Добавляем alt-тексты
        test_alts = {
            'ru': 'Тестовое изображение на русском',
            'en': 'Test image in English',
            'ua': 'Тестове зображення українською'
        }
        
        for lang, alt_text in test_alts.items():
            execute("""
                INSERT INTO images_alts (image_id, lang, alt_text) 
                VALUES (?, ?, ?)
            """, (image_id, lang, alt_text))
        print("✅ Alt-тексты добавлены")
        
        # Проверяем получение alt-текстов
        alts = query_all("SELECT lang, alt_text FROM images_alts WHERE image_id = ?", (image_id,))
        assert len(alts) == 3, f"Ожидалось 3 alt-текста, получено {len(alts)}"
        print("✅ Alt-тексты сохранены и получены")
        
        # Тестируем обновление
        execute("""
            UPDATE images_alts 
            SET alt_text = ? 
            WHERE image_id = ? AND lang = ?
        """, ("Обновленный текст", image_id, "ru"))
        
        updated_alt = query_one("""
            SELECT alt_text FROM images_alts 
            WHERE image_id = ? AND lang = ?
        """, (image_id, "ru"))
        assert updated_alt['alt_text'] == "Обновленный текст", "Alt-текст не обновился"
        print("✅ Alt-текст обновлен")
        
        # Тестируем удаление
        execute("DELETE FROM images_alts WHERE image_id = ? AND lang = ?", (image_id, "ua"))
        remaining_alts = query_all("SELECT lang FROM images_alts WHERE image_id = ?", (image_id,))
        assert len(remaining_alts) == 2, f"Ожидалось 2 alt-текста после удаления, получено {len(remaining_alts)}"
        print("✅ Alt-текст удален")
        
        # Очищаем тестовые данные
        execute("DELETE FROM images_alts WHERE image_id = ?", (image_id,))
        execute("DELETE FROM images WHERE id = ?", (image_id,))
        print("✅ Тестовые данные очищены")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования CRUD операций: {e}")
        return False


def test_template_variables():
    """Тест переменных шаблона"""
    print("🔍 Тестирование переменных шаблона...")
    
    try:
        # Тестируем CMS функцию
        cms_images = get_cms_images_for_template("ru")
        print(f"✅ CMS переменные изображений: {len(cms_images)} переменных")
        
        # Проверяем наличие основных переменных
        required_vars = ['logo', 'logo_alt', 'background', 'background_alt', 'favicon', 'favicon_alt']
        for var in required_vars:
            assert var in cms_images, f"Переменная {var} не найдена в CMS переменных"
        print("✅ CMS переменные содержат все необходимые ключи")
        
        # Проверяем переменные слайдера
        for i in range(1, 5):
            slider_var = f'slider{i}'
            slider_alt_var = f'slider{i}_alt'
            assert slider_var in cms_images, f"Переменная {slider_var} не найдена"
            assert slider_alt_var in cms_images, f"Переменная {slider_alt_var} не найдена"
        print("✅ Переменные слайдера присутствуют")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования переменных шаблона: {e}")
        return False


def test_foreign_key_constraints():
    """Тест ограничений внешних ключей"""
    print("🔍 Тестирование ограничений внешних ключей...")
    
    try:
        # Пытаемся добавить alt-текст для несуществующего изображения
        try:
            execute("""
                INSERT INTO images_alts (image_id, lang, alt_text) 
                VALUES (?, ?, ?)
            """, (99999, "ru", "Несуществующий alt"))
            print("❌ Ограничение внешнего ключа не работает")
            return False
        except Exception:
            print("✅ Ограничение внешнего ключа работает корректно")
        
        # Тестируем каскадное удаление
        # Создаем тестовое изображение
        execute("""
            INSERT INTO images (name, path, original_path, type, "order") 
            VALUES (?, ?, ?, ?, ?)
        """, ("cascade_test.jpg", "cascade.jpg", "cascade_orig.jpg", "logo", 0))
        
        image = query_one("SELECT id FROM images WHERE name = 'cascade_test.jpg'")
        image_id = image['id']
        
        # Добавляем alt-текст
        execute("""
            INSERT INTO images_alts (image_id, lang, alt_text) 
            VALUES (?, ?, ?)
        """, (image_id, "ru", "Тест каскадного удаления"))
        
        # Проверяем, что alt-текст добавлен
        alts_before = query_all("SELECT COUNT(*) as count FROM images_alts WHERE image_id = ?", (image_id,))
        assert alts_before[0]['count'] == 1, "Alt-текст не добавлен"
        
        # Удаляем изображение
        execute("DELETE FROM images WHERE id = ?", (image_id,))
        
        # Проверяем, что alt-текст удален каскадно
        alts_after = query_all("SELECT COUNT(*) as count FROM images_alts WHERE image_id = ?", (image_id,))
        assert alts_after[0]['count'] == 0, "Alt-текст не удален каскадно"
        print("✅ Каскадное удаление работает корректно")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования ограничений: {e}")
        return False


def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования системы alt-текстов для изображений")
    print("=" * 60)
    
    tests = [
        ("Структура базы данных", test_database_schema),
        ("Функции работы с изображениями", test_image_functions),
        ("CRUD операции с alt-текстами", test_alt_text_crud),
        ("Переменные шаблона", test_template_variables),
        ("Ограничения внешних ключей", test_foreign_key_constraints),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        try:
            if test_func():
                print(f"✅ {test_name} - ПРОЙДЕН")
                passed += 1
            else:
                print(f"❌ {test_name} - ПРОВАЛЕН")
        except Exception as e:
            print(f"💥 {test_name} - ОШИБКА: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Результаты тестирования: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
        return True
    else:
        print("⚠️  Некоторые тесты провалены")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
