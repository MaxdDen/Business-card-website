#!/usr/bin/env python3
"""
Минимальный тест SQL
"""

import sqlite3
import os

def test_minimal_sql():
    """Тест минимального SQL"""
    
    test_db = "test_minimal.db"
    
    try:
        if os.path.exists(test_db):
            os.remove(test_db)
        
        conn = sqlite3.connect(test_db)
        
        # Минимальный SQL для тестирования
        minimal_sql = """
        -- users
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          email TEXT NOT NULL UNIQUE,
          password_hash TEXT NOT NULL,
          role TEXT NOT NULL CHECK(role IN ('admin','editor')),
          created_at DATETIME NOT NULL DEFAULT (datetime('now'))
        );

        -- texts
        CREATE TABLE IF NOT EXISTS texts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          page TEXT NOT NULL,
          key TEXT NOT NULL,
          lang TEXT NOT NULL,
          value TEXT NOT NULL,
          UNIQUE(page, key, lang)
        );

        -- Header translations
        INSERT OR IGNORE INTO texts (page, key, lang, value) VALUES
        ('header', 'theme', 'en', 'Theme'),
        ('header', 'home', 'en', 'Home'),
        ('header', 'theme', 'ru', 'Тема'),
        ('header', 'home', 'ru', 'Главная'),
        ('header', 'theme', 'ua', 'Тема'),
        ('header', 'home', 'ua', 'Головна');
        """
        
        print("🔍 Тестируем минимальный SQL...")
        conn.executescript(minimal_sql)
        
        # Проверяем переводы
        cursor = conn.execute("SELECT * FROM texts WHERE page = 'header'")
        translations = cursor.fetchall()
        
        print(f"✅ Найдено {len(translations)} переводов header")
        for trans in translations:
            print(f"  {trans}")
        
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
    success = test_minimal_sql()
    exit(0 if success else 1)
