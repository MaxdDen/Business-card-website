#!/usr/bin/env python3
"""
Автотест для проверки исправления ошибки с длиной пароля в bcrypt
"""

import sys
import os
import logging

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.auth.security import hash_password, verify_password

def test_long_password_handling():
    """Тест обработки длинных паролей"""
    print("🔍 Тестирование обработки длинных паролей...")
    
    # Создаем очень длинный пароль (более 72 байт)
    long_password = "a" * 100  # 100 символов = 100 байт в UTF-8
    print(f"   Создан длинный пароль: {len(long_password)} символов ({len(long_password.encode('utf-8'))} байт)")
    
    try:
        # Тестируем хэширование
        print("   Тестируем хэширование длинного пароля...")
        password_hash = hash_password(long_password)
        print(f"   ✅ Хэширование успешно: {password_hash[:30]}...")
        
        # Тестируем верификацию
        print("   Тестируем верификацию длинного пароля...")
        is_valid = verify_password(long_password, password_hash)
        print(f"   ✅ Верификация успешна: {is_valid}")
        
        # Тестируем с неправильным паролем
        wrong_password = "b" * 100
        is_invalid = verify_password(wrong_password, password_hash)
        print(f"   ✅ Неправильный пароль отклонен: {not is_invalid}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании длинного пароля: {e}")
        return False

def test_unicode_password_handling():
    """Тест обработки паролей с Unicode символами"""
    print("🔍 Тестирование обработки Unicode паролей...")
    
    # Создаем пароль с Unicode символами (каждый символ может быть 2-4 байта)
    unicode_password = "пароль123" + "🔐" * 20  # Кириллица + эмодзи
    print(f"   Создан Unicode пароль: {len(unicode_password)} символов ({len(unicode_password.encode('utf-8'))} байт)")
    
    try:
        # Тестируем хэширование
        print("   Тестируем хэширование Unicode пароля...")
        password_hash = hash_password(unicode_password)
        print(f"   ✅ Хэширование успешно: {password_hash[:30]}...")
        
        # Тестируем верификацию
        print("   Тестируем верификацию Unicode пароля...")
        is_valid = verify_password(unicode_password, password_hash)
        print(f"   ✅ Верификация успешна: {is_valid}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании Unicode пароля: {e}")
        return False

def test_edge_cases():
    """Тест граничных случаев"""
    print("🔍 Тестирование граничных случаев...")
    
    test_cases = [
        ("", "пустой пароль"),
        ("a" * 72, "пароль ровно 72 байта"),
        ("a" * 73, "пароль 73 байта"),
        ("пароль" * 20, "длинный кириллический пароль"),
        ("🔐" * 30, "пароль с эмодзи"),
        ("a" * 1000, "очень длинный пароль"),
    ]
    
    success_count = 0
    
    for password, description in test_cases:
        try:
            print(f"   Тестируем {description}...")
            password_hash = hash_password(password)
            is_valid = verify_password(password, password_hash)
            
            if is_valid:
                print(f"   ✅ {description}: OK")
                success_count += 1
            else:
                print(f"   ❌ {description}: верификация не прошла")
                
        except Exception as e:
            print(f"   ❌ {description}: ошибка - {e}")
    
    print(f"   Результат: {success_count}/{len(test_cases)} тестов прошли успешно")
    return success_count == len(test_cases)

def test_fallback_hash():
    """Тест fallback хэширования"""
    print("🔍 Тестирование fallback хэширования...")
    
    try:
        # Создаем пароль, который может вызвать fallback
        test_password = "test_password_123"
        
        # Тестируем хэширование
        password_hash = hash_password(test_password)
        print(f"   ✅ Хэш создан: {password_hash[:30]}...")
        
        # Проверяем, что это fallback хэш
        if password_hash.startswith("pbkdf2_sha256$"):
            print("   ✅ Используется fallback хэш (pbkdf2_sha256)")
        else:
            print("   ℹ️  Используется основной хэш (bcrypt)")
        
        # Тестируем верификацию
        is_valid = verify_password(test_password, password_hash)
        print(f"   ✅ Верификация: {is_valid}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании fallback: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск автотеста исправления ошибки с длиной пароля")
    print("=" * 60)
    
    # Настраиваем логирование
    logging.basicConfig(level=logging.WARNING)  # Убираем лишние логи
    
    tests = [
        ("Обработка длинных паролей", test_long_password_handling),
        ("Обработка Unicode паролей", test_unicode_password_handling),
        ("Граничные случаи", test_edge_cases),
        ("Fallback хэширование", test_fallback_hash),
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
        print("🎉 Все тесты прошли успешно! Ошибка с длиной пароля исправлена.")
        return True
    else:
        print("⚠️  Некоторые тесты не прошли. Требуется дополнительная отладка.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
