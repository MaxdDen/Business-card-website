#!/usr/bin/env python3
"""
Автотест для проверки отсутствия ошибок bcrypt при запуске
"""

import sys
import os
import logging

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def test_security_module_import():
    """Тест импорта модуля безопасности без ошибок"""
    print("🔍 Тестирование импорта модуля безопасности...")
    
    try:
        # Импортируем модуль безопасности
        from app.auth.security import hash_password, verify_password
        print("   ✅ Модуль безопасности импортирован успешно")
        
        # Тестируем с длинным паролем
        long_password = "a" * 100
        print(f"   Тестируем с длинным паролем: {len(long_password)} символов")
        
        # Хэшируем пароль
        password_hash = hash_password(long_password)
        print(f"   ✅ Хэширование успешно: {password_hash[:30]}...")
        
        # Проверяем верификацию
        is_valid = verify_password(long_password, password_hash)
        print(f"   ✅ Верификация успешна: {is_valid}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка при импорте модуля безопасности: {e}")
        return False

def test_no_bcrypt_warnings():
    """Тест отсутствия предупреждений bcrypt"""
    print("🔍 Тестирование отсутствия предупреждений bcrypt...")
    
    # Настраиваем логирование для перехвата предупреждений
    import warnings
    import io
    import contextlib
    
    # Перехватываем stdout и stderr
    with contextlib.redirect_stdout(io.StringIO()) as stdout, \
         contextlib.redirect_stderr(io.StringIO()) as stderr:
        
        # Перехватываем предупреждения
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            try:
                from app.auth.security import hash_password, verify_password
                
                # Тестируем с разными паролями
                test_passwords = [
                    "short",
                    "a" * 100,
                    "пароль123",
                    "🔐" * 30,
                ]
                
                for password in test_passwords:
                    password_hash = hash_password(password)
                    verify_password(password, password_hash)
                
                # Проверяем, что нет предупреждений о bcrypt
                bcrypt_warnings = [warning for warning in w if 'bcrypt' in str(warning.message).lower()]
                
                if bcrypt_warnings:
                    print(f"   ❌ Найдены предупреждения bcrypt: {len(bcrypt_warnings)}")
                    for warning in bcrypt_warnings:
                        print(f"      - {warning.message}")
                    return False
                else:
                    print("   ✅ Предупреждения bcrypt отсутствуют")
                    return True
                    
            except Exception as e:
                print(f"   ❌ Ошибка при тестировании: {e}")
                return False

def test_password_processing():
    """Тест обработки паролей без ошибок"""
    print("🔍 Тестирование обработки паролей...")
    
    try:
        from app.auth.security import hash_password, verify_password
        
        # Тестируем с различными типами паролей
        test_cases = [
            ("", "пустой пароль"),
            ("a" * 72, "пароль 72 байта"),
            ("a" * 100, "пароль 100 байт"),
            ("пароль" * 20, "длинный кириллический пароль"),
            ("🔐" * 30, "пароль с эмодзи"),
            ("a" * 1000, "очень длинный пароль"),
        ]
        
        success_count = 0
        
        for password, description in test_cases:
            try:
                print(f"   Тестируем {description}...")
                
                # Хэшируем пароль
                password_hash = hash_password(password)
                
                # Проверяем верификацию
                is_valid = verify_password(password, password_hash)
                
                if is_valid:
                    print(f"   ✅ {description}: OK")
                    success_count += 1
                else:
                    print(f"   ❌ {description}: верификация не прошла")
                    
            except Exception as e:
                print(f"   ❌ {description}: ошибка - {e}")
        
        print(f"   Результат: {success_count}/{len(test_cases)} паролей обработаны успешно")
        return success_count == len(test_cases)
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании обработки паролей: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск автотеста отсутствия ошибок bcrypt")
    print("=" * 60)
    
    # Настраиваем логирование
    logging.basicConfig(level=logging.WARNING)  # Убираем лишние логи
    
    tests = [
        ("Импорт модуля безопасности", test_security_module_import),
        ("Отсутствие предупреждений bcrypt", test_no_bcrypt_warnings),
        ("Обработка паролей", test_password_processing),
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
        print("🎉 Все тесты прошли успешно! Ошибки bcrypt устранены.")
        return True
    else:
        print("⚠️  Некоторые тесты не прошли. Требуется дополнительная отладка.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
