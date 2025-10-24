#!/usr/bin/env python3
"""
Тест синтаксиса SQL файла
"""

import sqlite3
import os

def test_sql_syntax():
    """Проверить синтаксис SQL файла"""
    
    # Создаем временную базу данных
    test_db = "test_syntax.db"
    
    try:
        # Удаляем старую тестовую БД
        if os.path.exists(test_db):
            os.remove(test_db)
        
        # Создаем новую БД
        conn = sqlite3.connect(test_db)
        
        # Читаем SQL файл
        with open('app/database/init.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print("🔍 Проверяем синтаксис SQL файла...")
        
        # Выполняем SQL
        conn.executescript(sql_content)
        
        print("✅ SQL синтаксис корректен")
        
        # Проверяем, что таблицы созданы
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['users', 'texts', 'images', 'seo']
        missing_tables = [table for table in expected_tables if table not in tables]
        
        if missing_tables:
            print(f"❌ Отсутствуют таблицы: {missing_tables}")
            return False
        
        print(f"✅ Все таблицы созданы: {tables}")
        
        # Проверяем переводы header
        cursor = conn.execute("SELECT * FROM texts WHERE page = 'header'")
        header_translations = cursor.fetchall()
        
        if len(header_translations) == 0:
            print("❌ Переводы header не найдены")
            return False
        
        print(f"✅ Найдено {len(header_translations)} переводов header")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ SQL ошибка: {e}")
        return False
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
        if os.path.exists(test_db):
            os.remove(test_db)

if __name__ == "__main__":
    success = test_sql_syntax()
    exit(0 if success else 1)
