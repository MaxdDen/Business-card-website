#!/usr/bin/env python3
"""
Юнит-тесты для модуля валидации
Проверяет все функции валидации и безопасности
"""

import sys
import os
import unittest
from unittest.mock import patch

# Добавляем путь к модулям приложения
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.utils.validation import (
    sanitize_string, sanitize_html, validate_email, validate_password,
    validate_text_content, sanitize_filename, detect_sql_injection, detect_xss
)

class TestValidationUtils(unittest.TestCase):
    """Тесты для утилит валидации"""
    
    def test_sanitize_string_basic(self):
        """Тест базовой очистки строки"""
        # Нормальная строка
        result = sanitize_string("Hello World")
        self.assertEqual(result, "Hello World")
        
        # Пустая строка
        result = sanitize_string("")
        self.assertEqual(result, "")
        
        # None
        result = sanitize_string(None)
        self.assertEqual(result, "")
    
    def test_sanitize_string_control_chars(self):
        """Тест удаления управляющих символов"""
        # Строка с управляющими символами
        test_string = "Hello\x00\x01\x02World\x1f\x7f"
        result = sanitize_string(test_string)
        self.assertEqual(result, "HelloWorld")
        
        # Разрешенные символы должны остаться
        test_string = "Hello\n\r\tWorld"
        result = sanitize_string(test_string)
        self.assertEqual(result, "Hello\n\r\tWorld")
    
    def test_sanitize_string_max_length(self):
        """Тест ограничения длины"""
        long_string = "A" * 1000
        result = sanitize_string(long_string, max_length=100)
        self.assertEqual(len(result), 100)
        self.assertEqual(result, "A" * 100)
    
    def test_sanitize_string_trim(self):
        """Тест обрезки пробелов"""
        result = sanitize_string("  Hello World  ")
        self.assertEqual(result, "Hello World")
    
    def test_sanitize_html_basic(self):
        """Тест экранирования HTML"""
        # Обычные символы
        result = sanitize_html("Hello World")
        self.assertEqual(result, "Hello World")
        
        # HTML теги
        result = sanitize_html("<script>alert('xss')</script>")
        self.assertEqual(result, "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;")
        
        # Кавычки
        result = sanitize_html('He said "Hello"')
        self.assertEqual(result, 'He said &quot;Hello&quot;')
    
    def test_validate_email_valid(self):
        """Тест валидации корректных email"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@test.com"
        ]
        
        for email in valid_emails:
            is_valid, message = validate_email(email)
            self.assertTrue(is_valid, f"Email {email} должен быть валидным: {message}")
    
    def test_validate_email_invalid(self):
        """Тест валидации некорректных email"""
        invalid_emails = [
            "",
            "invalid",
            "@example.com",
            "test@",
            "test@.com",
            "test..test@example.com",
            "test@example..com",
            "a" * 300 + "@example.com"  # Слишком длинный
        ]
        
        for email in invalid_emails:
            is_valid, message = validate_email(email)
            self.assertFalse(is_valid, f"Email {email} должен быть невалидным")
    
    def test_validate_password_valid(self):
        """Тест валидации корректных паролей"""
        valid_passwords = [
            "password123",
            "MySecure123",
            "12345678",
            "abcdefgh",
            "P@ssw0rd!"
        ]
        
        for password in valid_passwords:
            is_valid, message = validate_password(password)
            self.assertTrue(is_valid, f"Пароль должен быть валидным: {message}")
    
    def test_validate_password_invalid(self):
        """Тест валидации некорректных паролей"""
        invalid_passwords = [
            "",
            "1234567",  # Слишком короткий
            "a" * 100,  # Слишком длинный
            "12345678",  # Только цифры
            "abcdefgh",  # Только буквы
            "!@#$%^&*"   # Только символы
        ]
        
        for password in invalid_passwords:
            is_valid, message = validate_password(password)
            self.assertFalse(is_valid, f"Пароль должен быть невалидным: {message}")
    
    def test_validate_text_content_valid(self):
        """Тест валидации корректного текстового контента"""
        valid_texts = [
            "Hello World",
            "A" * 1000,  # Максимальная длина
            "Текст с кириллицей",
            "Text with\nnewlines"
        ]
        
        for text in valid_texts:
            is_valid, message = validate_text_content(text)
            self.assertTrue(is_valid, f"Текст должен быть валидным: {message}")
    
    def test_validate_text_content_invalid(self):
        """Тест валидации некорректного текстового контента"""
        invalid_texts = [
            "A" * 10001,  # Слишком длинный
            None,
            ""  # Пустой текст
        ]
        
        for text in invalid_texts:
            is_valid, message = validate_text_content(text)
            self.assertFalse(is_valid, f"Текст должен быть невалидным: {message}")
    
    def test_sanitize_filename_basic(self):
        """Тест очистки имени файла"""
        # Нормальное имя
        result = sanitize_filename("image.jpg")
        self.assertEqual(result, "image.jpg")
        
        # Опасные символы
        result = sanitize_filename("../../../etc/passwd")
        self.assertEqual(result, "etcpasswd")
        
        # Путь traversal
        result = sanitize_filename("..\\..\\windows\\system32")
        self.assertEqual(result, "windowssystem32")
    
    def test_sanitize_filename_length(self):
        """Тест ограничения длины имени файла"""
        long_name = "A" * 300 + ".jpg"
        result = sanitize_filename(long_name)
        self.assertLessEqual(len(result), 255)
    
    def test_detect_sql_injection_clean(self):
        """Тест обнаружения SQL инъекций в чистых строках"""
        clean_inputs = [
            "Hello World",
            "user@example.com",
            "normal text",
            "SELECT * FROM users"  # Не инъекция, если в кавычках
        ]
        
        for text in clean_inputs:
            is_injection, message = detect_sql_injection(text)
            self.assertFalse(is_injection, f"Текст не должен определяться как SQL инъекция: {message}")
    
    def test_detect_sql_injection_malicious(self):
        """Тест обнаружения SQL инъекций"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "1' UNION SELECT * FROM users--",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --"
        ]
        
        for text in malicious_inputs:
            is_injection, message = detect_sql_injection(text)
            self.assertTrue(is_injection, f"Текст должен определяться как SQL инъекция: {message}")
    
    def test_detect_xss_clean(self):
        """Тест обнаружения XSS в чистых строках"""
        clean_inputs = [
            "Hello World",
            "normal text",
            "user@example.com",
            "Simple HTML: <b>bold</b>"
        ]
        
        for text in clean_inputs:
            is_xss, message = detect_xss(text)
            self.assertFalse(is_xss, f"Текст не должен определяться как XSS: {message}")
    
    def test_detect_xss_malicious(self):
        """Тест обнаружения XSS атак"""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<iframe src=javascript:alert('xss')></iframe>",
            "onload=alert('xss')",
            "<svg onload=alert('xss')>"
        ]
        
        for text in malicious_inputs:
            is_xss, message = detect_xss(text)
            self.assertTrue(is_xss, f"Текст должен определяться как XSS: {message}")
    
    def test_edge_cases(self):
        """Тест граничных случаев"""
        # Пустые значения
        self.assertEqual(sanitize_string(""), "")
        self.assertEqual(sanitize_string(None), "")
        
        # Unicode символы
        unicode_text = "Привет 世界 🌍"
        result = sanitize_string(unicode_text)
        self.assertEqual(result, unicode_text)
        
        # Очень длинные строки
        long_text = "A" * 10000
        result = sanitize_string(long_text, max_length=100)
        self.assertEqual(len(result), 100)
    
    def test_performance(self):
        """Тест производительности на больших данных"""
        import time
        
        # Большой текст
        large_text = "A" * 10000
        
        start_time = time.time()
        result = sanitize_string(large_text)
        end_time = time.time()
        
        # Обработка должна быть быстрой (< 0.1 сек)
        self.assertLess(end_time - start_time, 0.1)
        self.assertEqual(len(result), 10000)


class TestValidationIntegration(unittest.TestCase):
    """Интеграционные тесты валидации"""
    
    def test_validation_pipeline(self):
        """Тест полного пайплайна валидации"""
        # Исходные данные
        user_input = "  <script>alert('xss')</script>  "
        email = "test@example.com"
        password = "password123"
        
        # Очистка и валидация
        cleaned_input = sanitize_string(user_input)
        html_safe = sanitize_html(cleaned_input)
        
        email_valid, _ = validate_email(email)
        password_valid, _ = validate_password(password)
        
        # Проверки
        self.assertTrue(email_valid)
        self.assertTrue(password_valid)
        self.assertNotIn("<script>", html_safe)
        self.assertIn("&lt;script&gt;", html_safe)
    
    def test_security_validation_combined(self):
        """Тест комбинированной проверки безопасности"""
        # Потенциально опасные входные данные
        dangerous_inputs = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "admin' OR '1'='1"
        ]
        
        for dangerous_input in dangerous_inputs:
            # Проверяем SQL инъекции
            is_sql_injection, _ = detect_sql_injection(dangerous_input)
            self.assertTrue(is_sql_injection, f"Должна обнаруживаться SQL инъекция: {dangerous_input}")
            
            # Проверяем XSS
            is_xss, _ = detect_xss(dangerous_input)
            if "<script>" in dangerous_input:
                self.assertTrue(is_xss, f"Должна обнаруживаться XSS: {dangerous_input}")
            
            # Проверяем очистку
            cleaned = sanitize_string(dangerous_input)
            self.assertNotEqual(cleaned, dangerous_input)


if __name__ == "__main__":
    # Настройка тестирования
    unittest.main(verbosity=2)
