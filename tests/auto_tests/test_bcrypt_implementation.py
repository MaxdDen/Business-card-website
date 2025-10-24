#!/usr/bin/env python3
"""
Автотест для проверки корректного использования bcrypt в проекте
Проверяет, что используется только bcrypt для хеширования паролей по best practices
"""

import sys
import os
import warnings
import traceback

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def test_bcrypt_import():
    """Тест импорта bcrypt"""
    print("🔍 Тестирование импорта bcrypt...")
    try:
        import bcrypt
        print(f"   ✅ bcrypt импортирован успешно, версия: {bcrypt.__version__}")
        return True
    except ImportError as e:
        print(f"   ❌ Ошибка импорта bcrypt: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Неожиданная ошибка при импорте bcrypt: {e}")
        return False

def test_no_passlib_usage():
    """Тест отсутствия использования passlib"""
    print("🔍 Тестирование отсутствия passlib...")
    try:
        # Проверяем, что passlib не импортируется в основных модулях
        from app.auth.security import hash_password, verify_password
        
        # Проверяем, что в коде нет упоминаний passlib
        import inspect
        source = inspect.getsource(hash_password)
        if 'passlib' in source.lower():
            print("   ❌ Найдено использование passlib в hash_password")
            return False
            
        source = inspect.getsource(verify_password)
        if 'passlib' in source.lower():
            print("   ❌ Найдено использование passlib в verify_password")
            return False
            
        print("   ✅ passlib не используется в основных функциях")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка при проверке passlib: {e}")
        return False

def test_bcrypt_functionality():
    """Тест функциональности bcrypt"""
    print("🔍 Тестирование функциональности bcrypt...")
    try:
        from app.auth.security import hash_password, verify_password
        
        # Тестируем различные пароли
        test_passwords = [
            "simple_password",
            "complex_P@ssw0rd!",
            "пароль_с_кириллицей",
            "password_with_72_chars_" + "x" * 40,  # 72 символа
            "very_long_password_" + "x" * 100,  # > 72 символов
        ]
        
        for password in test_passwords:
            print(f"   Тестируем пароль: {password[:20]}...")
            
            # Хешируем пароль
            password_hash = hash_password(password)
            print(f"   ✅ Хэш создан: {password_hash[:30]}...")
            
            # Проверяем, что хэш начинается с $2b$ (bcrypt)
            if not password_hash.startswith('$2b$'):
                print(f"   ❌ Хэш не является bcrypt: {password_hash[:20]}...")
                return False
                
            # Проверяем верификацию
            is_valid = verify_password(password, password_hash)
            if not is_valid:
                print(f"   ❌ Верификация не прошла для пароля: {password[:20]}...")
                return False
                
            # Проверяем, что неправильный пароль не проходит
            wrong_password = password + "_wrong"
            is_invalid = verify_password(wrong_password, password_hash)
            if is_invalid:
                print(f"   ❌ Неправильный пароль прошел верификацию: {wrong_password[:20]}...")
                return False
                
            print(f"   ✅ Пароль {password[:20]}... обработан корректно")
        
        print("   ✅ Все тесты функциональности bcrypt прошли успешно")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании функциональности bcrypt: {e}")
        traceback.print_exc()
        return False

def test_bcrypt_security():
    """Тест безопасности bcrypt"""
    print("🔍 Тестирование безопасности bcrypt...")
    try:
        from app.auth.security import hash_password, verify_password
        
        # Тестируем, что одинаковые пароли дают разные хэши (соль)
        password = "test_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        if hash1 == hash2:
            print("   ❌ Одинаковые хэши для одного пароля (отсутствует соль)")
            return False
            
        # Проверяем, что оба хэша валидны
        if not verify_password(password, hash1) or not verify_password(password, hash2):
            print("   ❌ Один из хэшей не прошел верификацию")
            return False
            
        print("   ✅ Соль работает корректно - разные хэши для одного пароля")
        
        # Тестируем ограничение длины пароля (72 байта)
        long_password = "x" * 100  # 100 символов
        hash_long = hash_password(long_password)
        is_valid_long = verify_password(long_password, hash_long)
        
        if not is_valid_long:
            print("   ❌ Длинный пароль не прошел верификацию")
            return False
            
        print("   ✅ Обработка длинных паролей работает корректно")
        
        # Тестируем Unicode пароли
        unicode_password = "пароль_с_эмодзи_🚀_и_кириллицей"
        hash_unicode = hash_password(unicode_password)
        is_valid_unicode = verify_password(unicode_password, hash_unicode)
        
        if not is_valid_unicode:
            print("   ❌ Unicode пароль не прошел верификацию")
            return False
            
        print("   ✅ Unicode пароли обрабатываются корректно")
        
        print("   ✅ Все тесты безопасности bcrypt прошли успешно")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании безопасности bcrypt: {e}")
        traceback.print_exc()
        return False

def test_bcrypt_performance():
    """Тест производительности bcrypt"""
    print("🔍 Тестирование производительности bcrypt...")
    try:
        from app.auth.security import hash_password, verify_password
        import time
        
        password = "performance_test_password"
        
        # Тестируем время хеширования
        start_time = time.time()
        password_hash = hash_password(password)
        hash_time = time.time() - start_time
        
        print(f"   ⏱️  Время хеширования: {hash_time:.3f} секунд")
        
        # bcrypt должен быть медленным для безопасности (обычно 0.1-0.5 сек)
        if hash_time < 0.05:
            print("   ⚠️  Хеширование слишком быстрое, возможно небезопасно")
        elif hash_time > 2.0:
            print("   ⚠️  Хеширование слишком медленное")
        else:
            print("   ✅ Время хеширования в нормальном диапазоне")
        
        # Тестируем время верификации
        start_time = time.time()
        is_valid = verify_password(password, password_hash)
        verify_time = time.time() - start_time
        
        print(f"   ⏱️  Время верификации: {verify_time:.3f} секунд")
        
        if not is_valid:
            print("   ❌ Верификация не прошла")
            return False
            
        print("   ✅ Производительность bcrypt в норме")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании производительности bcrypt: {e}")
        return False

def test_no_bcrypt_warnings():
    """Тест отсутствия предупреждений bcrypt"""
    print("🔍 Тестирование отсутствия предупреждений bcrypt...")
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            from app.auth.security import hash_password, verify_password
            
            # Выполняем операции с паролями
            password = "test_warning_password"
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
        print(f"   ❌ Ошибка при проверке предупреждений bcrypt: {e}")
        return False

def main():
    """Основная функция автотеста"""
    print("🚀 Запуск автотеста корректного использования bcrypt")
    print("=" * 60)
    
    tests = [
        ("Импорт bcrypt", test_bcrypt_import),
        ("Отсутствие passlib", test_no_passlib_usage),
        ("Функциональность bcrypt", test_bcrypt_functionality),
        ("Безопасность bcrypt", test_bcrypt_security),
        ("Производительность bcrypt", test_bcrypt_performance),
        ("Отсутствие предупреждений", test_no_bcrypt_warnings),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - ПРОЙДЕН")
            else:
                print(f"❌ {test_name} - ПРОВАЛЕН")
        except Exception as e:
            print(f"❌ {test_name} - ОШИБКА: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"📊 Результаты: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты прошли успешно! bcrypt реализован корректно.")
        return True
    else:
        print(f"⚠️  {total - passed} тестов провалено. Требуется исправление.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
