#!/usr/bin/env python3
"""
Скрипт для создания тестового пользователя
"""
from app.database.db import execute
from app.auth.security import hash_password

def create_test_user():
    """Создать тестового пользователя"""
    email = "admin@example.com"
    password = "admin123"
    role = "admin"
    
    # Проверяем, существует ли уже пользователь
    from app.database.db import query_one
    existing_user = query_one("SELECT id FROM users WHERE email = ?", (email,))
    
    if existing_user:
        print(f"Пользователь {email} уже существует")
        return
    
    # Создаем пользователя
    password_hash = hash_password(password)
    user_id = execute(
        "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
        (email, password_hash, role)
    )
    
    print(f"Создан пользователь:")
    print(f"  Email: {email}")
    print(f"  Пароль: {password}")
    print(f"  Роль: {role}")
    print(f"  ID: {user_id}")

if __name__ == "__main__":
    create_test_user()

