#!/usr/bin/env python3
"""
Автотест для проверки управления пользователями (Этап 8)
Проверяет:
- API endpoints для управления пользователями
- Проверку роли admin для доступа
- Создание, удаление и сброс пароля пользователей
- UI интерфейс управления пользователями
"""

import requests
import json
import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class UsersManagementTest:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.admin_token = None
        self.editor_token = None
        self.test_user_id = None
        
    def log(self, message):
        """Логирование с временной меткой"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def login_admin(self):
        """Вход под admin пользователем"""
        self.log("🔐 Вход под admin пользователем...")
        
        # Сначала регистрируем admin пользователя, если его нет
        register_data = {
            "email": "admin@test.com",
            "password": "admin123456"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/register", data=register_data)
            if response.status_code == 200:
                self.log("✅ Admin пользователь зарегистрирован")
            else:
                self.log("ℹ️ Admin пользователь уже существует")
        except:
            pass
        
        # Входим под admin
        login_data = {
            "email": "admin@test.com",
            "password": "admin123456"
        }
        
        response = self.session.post(f"{self.base_url}/login", data=login_data)
        if response.status_code == 200:
            self.log("✅ Успешный вход под admin")
            return True
        else:
            self.log(f"❌ Ошибка входа под admin: {response.status_code}")
            return False
    
    def login_editor(self):
        """Вход под editor пользователем"""
        self.log("🔐 Вход под editor пользователем...")
        
        # Сначала создаем editor пользователя через admin
        if not self.admin_token:
            self.log("❌ Нет доступа к admin токену")
            return False
        
        editor_data = {
            "email": "editor@test.com",
            "password": "editor123456",
            "role": "editor"
        }
        
        response = self.session.post(f"{self.base_url}/cms/api/users", data=editor_data)
        if response.status_code == 200:
            self.log("✅ Editor пользователь создан")
        else:
            self.log(f"❌ Ошибка создания editor пользователя: {response.status_code}")
            return False
        
        # Входим под editor
        login_data = {
            "email": "editor@test.com",
            "password": "editor123456"
        }
        
        response = self.session.post(f"{self.base_url}/login", data=login_data)
        if response.status_code == 200:
            self.log("✅ Успешный вход под editor")
            return True
        else:
            self.log(f"❌ Ошибка входа под editor: {response.status_code}")
            return False
    
    def test_get_users_admin(self):
        """Тест получения списка пользователей (admin)"""
        self.log("📋 Тест получения списка пользователей (admin)...")
        
        response = self.session.get(f"{self.base_url}/cms/api/users")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                users = data.get("users", [])
                self.log(f"✅ Получен список пользователей: {len(users)} пользователей")
                return True
            else:
                self.log(f"❌ Ошибка получения пользователей: {data.get('message')}")
                return False
        else:
            self.log(f"❌ Ошибка HTTP: {response.status_code}")
            return False
    
    def test_get_users_editor(self):
        """Тест получения списка пользователей (editor) - должен быть запрещен"""
        self.log("🚫 Тест получения списка пользователей (editor) - должен быть запрещен...")
        
        response = self.session.get(f"{self.base_url}/cms/api/users")
        if response.status_code == 403:
            self.log("✅ Доступ корректно запрещен для editor")
            return True
        else:
            self.log(f"❌ Неожиданный статус: {response.status_code}")
            return False
    
    def test_create_user(self):
        """Тест создания пользователя"""
        self.log("👤 Тест создания пользователя...")
        
        user_data = {
            "email": "testuser@example.com",
            "password": "testpass123",
            "role": "editor"
        }
        
        response = self.session.post(f"{self.base_url}/cms/api/users", data=user_data)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                self.log("✅ Пользователь успешно создан")
                return True
            else:
                self.log(f"❌ Ошибка создания пользователя: {data.get('message')}")
                return False
        else:
            self.log(f"❌ Ошибка HTTP: {response.status_code}")
            return False
    
    def test_create_user_long_password(self):
        """Тест создания пользователя с длинным паролем (должен быть отклонен)"""
        self.log("🔒 Тест создания пользователя с длинным паролем...")
        
        # Создаем пароль длиннее 72 символов
        long_password = "a" * 80
        
        user_data = {
            "email": "longpass@example.com",
            "password": long_password,
            "role": "editor"
        }
        
        response = self.session.post(f"{self.base_url}/cms/api/users", data=user_data)
        if response.status_code == 200:
            data = response.json()
            if not data.get("success") and "72 байтов" in data.get("message", ""):
                self.log("✅ Корректно обработана попытка создания пользователя с длинным паролем")
                return True
            else:
                self.log(f"❌ Неожиданный ответ: {data}")
                return False
        else:
            self.log(f"❌ Ошибка HTTP: {response.status_code}")
            return False
    
    def test_create_duplicate_user(self):
        """Тест создания пользователя с существующим email"""
        self.log("🔄 Тест создания пользователя с существующим email...")
        
        user_data = {
            "email": "testuser@example.com",  # Тот же email
            "password": "testpass123",
            "role": "editor"
        }
        
        response = self.session.post(f"{self.base_url}/cms/api/users", data=user_data)
        if response.status_code == 200:
            data = response.json()
            if not data.get("success") and "уже существует" in data.get("message", ""):
                self.log("✅ Корректно обработана попытка создания дубликата")
                return True
            else:
                self.log(f"❌ Неожиданный ответ: {data}")
                return False
        else:
            self.log(f"❌ Ошибка HTTP: {response.status_code}")
            return False
    
    def test_create_user_editor_access(self):
        """Тест создания пользователя editor'ом - должен быть запрещен"""
        self.log("🚫 Тест создания пользователя editor'ом - должен быть запрещен...")
        
        user_data = {
            "email": "unauthorized@example.com",
            "password": "testpass123",
            "role": "editor"
        }
        
        response = self.session.post(f"{self.base_url}/cms/api/users", data=user_data)
        if response.status_code == 403:
            self.log("✅ Доступ корректно запрещен для editor")
            return True
        else:
            self.log(f"❌ Неожиданный статус: {response.status_code}")
            return False
    
    def test_reset_password(self):
        """Тест сброса пароля пользователя"""
        self.log("🔑 Тест сброса пароля пользователя...")
        
        # Сначала получаем список пользователей, чтобы найти ID тестового пользователя
        response = self.session.get(f"{self.base_url}/cms/api/users")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                users = data.get("users", [])
                test_user = None
                for user in users:
                    if user["email"] == "testuser@example.com":
                        test_user = user
                        break
                
                if test_user:
                    self.test_user_id = test_user["id"]
                    self.log(f"✅ Найден тестовый пользователь с ID: {self.test_user_id}")
                    
                    # Сбрасываем пароль
                    reset_data = {
                        "new_password": "newpassword123"
                    }
                    
                    response = self.session.post(f"{self.base_url}/cms/api/users/{self.test_user_id}/reset-password", data=reset_data)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success"):
                            self.log("✅ Пароль успешно сброшен")
                            return True
                        else:
                            self.log(f"❌ Ошибка сброса пароля: {data.get('message')}")
                            return False
                    else:
                        self.log(f"❌ Ошибка HTTP: {response.status_code}")
                        return False
                else:
                    self.log("❌ Тестовый пользователь не найден")
                    return False
            else:
                self.log(f"❌ Ошибка получения пользователей: {data.get('message')}")
                return False
        else:
            self.log(f"❌ Ошибка HTTP: {response.status_code}")
            return False
    
    def test_delete_user(self):
        """Тест удаления пользователя"""
        self.log("🗑️ Тест удаления пользователя...")
        
        if not self.test_user_id:
            self.log("❌ Нет ID тестового пользователя")
            return False
        
        response = self.session.delete(f"{self.base_url}/cms/api/users/{self.test_user_id}")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                self.log("✅ Пользователь успешно удален")
                return True
            else:
                self.log(f"❌ Ошибка удаления пользователя: {data.get('message')}")
                return False
        else:
            self.log(f"❌ Ошибка HTTP: {response.status_code}")
            return False
    
    def test_delete_self(self):
        """Тест попытки удаления самого себя"""
        self.log("🔄 Тест попытки удаления самого себя...")
        
        # Получаем список пользователей, чтобы найти ID admin пользователя
        response = self.session.get(f"{self.base_url}/cms/api/users")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                users = data.get("users", [])
                admin_user = None
                for user in users:
                    if user["email"] == "admin@test.com":
                        admin_user = user
                        break
                
                if admin_user:
                    admin_id = admin_user["id"]
                    
                    # Пытаемся удалить самого себя
                    response = self.session.delete(f"{self.base_url}/cms/api/users/{admin_id}")
                    if response.status_code == 200:
                        data = response.json()
                        if not data.get("success") and "самого себя" in data.get("message", ""):
                            self.log("✅ Корректно обработана попытка удаления самого себя")
                            return True
                        else:
                            self.log(f"❌ Неожиданный ответ: {data}")
                            return False
                    else:
                        self.log(f"❌ Ошибка HTTP: {response.status_code}")
                        return False
                else:
                    self.log("❌ Admin пользователь не найден")
                    return False
            else:
                self.log(f"❌ Ошибка получения пользователей: {data.get('message')}")
                return False
        else:
            self.log(f"❌ Ошибка HTTP: {response.status_code}")
            return False
    
    def test_users_page_access(self):
        """Тест доступа к странице управления пользователями"""
        self.log("🌐 Тест доступа к странице управления пользователями...")
        
        # Тест доступа admin
        response = self.session.get(f"{self.base_url}/cms/users")
        if response.status_code == 200:
            self.log("✅ Admin имеет доступ к странице пользователей")
        else:
            self.log(f"❌ Admin не имеет доступа: {response.status_code}")
            return False
        
        return True
    
    def test_users_page_editor_access(self):
        """Тест доступа editor к странице управления пользователями - должен быть запрещен"""
        self.log("🚫 Тест доступа editor к странице управления пользователями...")
        
        response = self.session.get(f"{self.base_url}/cms/users")
        if response.status_code == 403:
            self.log("✅ Доступ корректно запрещен для editor")
            return True
        else:
            self.log(f"❌ Неожиданный статус: {response.status_code}")
            return False
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        self.log("🚀 Запуск автотестов управления пользователями")
        self.log("=" * 60)
        
        tests = []
        
        # Тесты с admin доступом
        self.log("\n📋 ТЕСТЫ С ADMIN ДОСТУПОМ:")
        self.log("-" * 40)
        
        if self.login_admin():
            tests.append(("Получение списка пользователей (admin)", self.test_get_users_admin()))
            tests.append(("Создание пользователя", self.test_create_user()))
            tests.append(("Создание пользователя с длинным паролем", self.test_create_user_long_password()))
            tests.append(("Создание дубликата пользователя", self.test_create_duplicate_user()))
            tests.append(("Сброс пароля пользователя", self.test_reset_password()))
            tests.append(("Удаление пользователя", self.test_delete_user()))
            tests.append(("Попытка удаления самого себя", self.test_delete_self()))
            tests.append(("Доступ к странице пользователей (admin)", self.test_users_page_access()))
        else:
            self.log("❌ Не удалось войти под admin, пропускаем тесты")
        
        # Тесты с editor доступом
        self.log("\n📋 ТЕСТЫ С EDITOR ДОСТУПОМ:")
        self.log("-" * 40)
        
        if self.login_editor():
            tests.append(("Получение списка пользователей (editor)", self.test_get_users_editor()))
            tests.append(("Создание пользователя (editor)", self.test_create_user_editor_access()))
            tests.append(("Доступ к странице пользователей (editor)", self.test_users_page_editor_access()))
        else:
            self.log("❌ Не удалось войти под editor, пропускаем тесты")
        
        # Результаты
        self.log("\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        self.log("=" * 60)
        
        passed = 0
        total = len(tests)
        
        for test_name, result in tests:
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            self.log(f"{status}: {test_name}")
            if result:
                passed += 1
        
        self.log(f"\n📈 ИТОГО: {passed}/{total} тестов пройдено")
        
        if passed == total:
            self.log("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            return True
        else:
            self.log(f"⚠️ ПРОВАЛЕНО {total - passed} тестов")
            return False

def main():
    """Главная функция для запуска тестов"""
    print("🧪 АВТОТЕСТ УПРАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯМИ")
    print("=" * 60)
    print("Этот тест проверяет:")
    print("• API endpoints для управления пользователями")
    print("• Проверку роли admin для доступа")
    print("• Создание, удаление и сброс пароля пользователей")
    print("• UI интерфейс управления пользователями")
    print("• Разделение доступа по ролям")
    print("=" * 60)
    
    # Проверяем доступность сервера
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Сервер доступен")
        else:
            print("❌ Сервер недоступен или не отвечает")
            return False
    except:
        print("❌ Не удается подключиться к серверу")
        print("Убедитесь, что сервер запущен на http://localhost:8000")
        return False
    
    # Запускаем тесты
    test = UsersManagementTest()
    success = test.run_all_tests()
    
    if success:
        print("\n🎯 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Этап 8 реализован успешно.")
        return True
    else:
        print("\n❌ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ. Проверьте реализацию.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
