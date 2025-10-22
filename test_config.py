#!/usr/bin/env python3
"""
Тест конфигурации языков
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.site.config import get_supported_languages, get_default_language

def test_config():
    """Тест конфигурации"""
    print("🧪 Тест конфигурации языков...")
    
    supported_languages = get_supported_languages()
    default_language = get_default_language()
    
    print(f"📋 Поддерживаемые языки: {supported_languages}")
    print(f"📋 Язык по умолчанию: {default_language}")
    
    # Проверяем, что язык по умолчанию входит в поддерживаемые
    if default_language in supported_languages:
        print(f"✅ Язык по умолчанию '{default_language}' поддерживается")
    else:
        print(f"❌ Язык по умолчанию '{default_language}' НЕ поддерживается")
    
    # Проверяем порядок языков
    print(f"📋 Порядок языков: {supported_languages}")
    print(f"📋 Первый язык: {supported_languages[0] if supported_languages else 'None'}")
    print(f"📋 Последний язык: {supported_languages[-1] if supported_languages else 'None'}")

if __name__ == "__main__":
    test_config()
