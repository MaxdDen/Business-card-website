#!/usr/bin/env python3
"""
Автотест для проверки исправления ошибки при запуске приложения
"""

import sys
import os
import logging
import subprocess
import time

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def test_startup_without_errors():
    """Тест запуска приложения без ошибок с длинными паролями"""
    print("🔍 Тестирование запуска приложения...")
    
    try:
        # Импортируем модули для проверки
        from app.auth.security import hash_password, verify_password
        
        # Тестируем с длинным паролем
        long_password = "a" * 100
        print(f"   Тестируем с длинным паролем: {len(long_password)} символов")
        
        # Хэшируем пароль
        password_hash = hash_password(long_password)
        print(f"   ✅ Хэширование успешно: {password_hash[:30]}...")
        
        # Проверяем верификацию
        is_valid = verify_password(long_password, password_hash)
        print(f"   ✅ Верификация успешна: {is_valid}")
        
        # Тестируем с Unicode паролем
        unicode_password = "пароль" + "🔐" * 20
        print(f"   Тестируем с Unicode паролем: {len(unicode_password)} символов")
        
        unicode_hash = hash_password(unicode_password)
        print(f"   ✅ Unicode хэширование успешно: {unicode_hash[:30]}...")
        
        unicode_valid = verify_password(unicode_password, unicode_hash)
        print(f"   ✅ Unicode верификация успешна: {unicode_valid}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании: {e}")
        return False

def test_import_modules():
    """Тест импорта всех модулей без ошибок"""
    print("🔍 Тестирование импорта модулей...")
    
    modules_to_test = [
        "app.main",
        "app.auth.security", 
        "app.auth.routes",
        "app.database.db",
        "app.cms.routes",
        "app.site.routes"
    ]
    
    success_count = 0
    
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"   ✅ {module_name}: импорт успешен")
            success_count += 1
        except Exception as e:
            print(f"   ❌ {module_name}: ошибка импорта - {e}")
    
    print(f"   Результат: {success_count}/{len(modules_to_test)} модулей импортированы успешно")
    return success_count == len(modules_to_test)

def test_security_functions():
    """Тест функций безопасности"""
    print("🔍 Тестирование функций безопасности...")
    
    try:
        from app.auth.security import hash_password, verify_password, create_access_token, decode_token
        
        # Тест с разными типами паролей
        test_passwords = [
            "short",
            "a" * 72,  # ровно 72 байта
            "a" * 100,  # больше 72 байт
            "пароль123",
            "🔐" * 30,
            "",  # пустой пароль
        ]
        
        success_count = 0
        
        for password in test_passwords:
            try:
                # Хэшируем
                password_hash = hash_password(password)
                
                # Проверяем верификацию
                is_valid = verify_password(password, password_hash)
                
                if is_valid:
                    print(f"   ✅ Пароль '{password[:20]}...': OK")
                    success_count += 1
                else:
                    print(f"   ❌ Пароль '{password[:20]}...': верификация не прошла")
                    
            except Exception as e:
                print(f"   ❌ Пароль '{password[:20]}...': ошибка - {e}")
        
        print(f"   Результат: {success_count}/{len(test_passwords)} паролей обработаны успешно")
        return success_count == len(test_passwords)
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании функций безопасности: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск автотеста исправления ошибки при запуске")
    print("=" * 60)
    
    # Настраиваем логирование
    logging.basicConfig(level=logging.WARNING)  # Убираем лишние логи
    
    tests = [
        ("Импорт модулей", test_import_modules),
        ("Функции безопасности", test_security_functions),
        ("Запуск без ошибок", test_startup_without_errors),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                print(f"✅ {test_name}: ПРОЙДЕН")
                passed += 1
            else:
                print(f"❌ {test_name}: ПРОВАЛЕН")
        except Exception as e:
            print(f"❌ {test_name}: ОШИБКА - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 РЕЗУЛЬТАТ: {passed}/{total} тестов прошли успешно")
    
    if passed == total:
        print("🎉 Все тесты прошли успешно! Ошибка при запуске исправлена.")
        return True
    else:
        print("⚠️  Некоторые тесты не прошли. Требуется дополнительная отладка.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
