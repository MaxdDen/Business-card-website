#!/usr/bin/env python3
"""
Общие фикстуры для pytest
Предоставляет общие настройки и фикстуры для всех тестов
"""

import os
import sys
import tempfile
import sqlite3
import pytest
import requests
from pathlib import Path
from unittest.mock import patch, MagicMock

# Добавляем путь к модулям приложения
sys.path.insert(0, str(Path(__file__).parent.parent))

# Импорты приложения
from app.database.db import ensure_database_initialized, get_connection
from app.utils.cache import TextCache, SEOCache
from app.utils.validation import validate_email, validate_password


@pytest.fixture(scope="session")
def test_base_url():
    """Базовый URL для тестов"""
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def test_session():
    """Сессия requests для тестов"""
    session = requests.Session()
    
    # Настройка retry стратегии
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    yield session
    session.close()


@pytest.fixture(scope="function")
def temp_database():
    """Временная база данных для тестов"""
    # Создаем временную базу данных
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    db_path = temp_db.name
    
    # Патчим путь к БД
    with patch('app.database.db.DB_PATH', db_path):
        # Инициализируем БД
        ensure_database_initialized()
        yield db_path
    
    # Очищаем после теста
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture(scope="function")
def test_connection(temp_database):
    """Подключение к тестовой БД"""
    with get_connection() as conn:
        yield conn


@pytest.fixture(scope="function")
def test_cache():
    """Тестовый кэш"""
    cache = TextCache(default_ttl=1)  # Короткий TTL для тестов
    yield cache
    cache.clear()


@pytest.fixture(scope="function")
def test_seo_cache():
    """Тестовый SEO кэш"""
    cache = SEOCache(default_ttl=1)  # Короткий TTL для тестов
    yield cache
    cache.clear()


@pytest.fixture(scope="function")
def test_user_data():
    """Тестовые данные пользователя"""
    return {
        "email": f"test_{pytest.current_test_id()}@example.com",
        "password": "testpassword123",
        "role": "editor"
    }


@pytest.fixture(scope="function")
def test_text_data():
    """Тестовые данные для текстов"""
    return {
        "page": "home",
        "lang": "ru",
        "texts": {
            "title": "Тестовый заголовок",
            "subtitle": "Тестовый подзаголовок",
            "description": "Тестовое описание"
        }
    }


@pytest.fixture(scope="function")
def test_seo_data():
    """Тестовые данные для SEO"""
    return {
        "page": "home",
        "lang": "ru",
        "seo": {
            "title": "SEO заголовок",
            "description": "SEO описание",
            "keywords": "тест, seo, ключевые слова"
        }
    }


@pytest.fixture(scope="function")
def test_image_data():
    """Тестовые данные для изображения (1x1 PNG)"""
    return {
        "data": b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82',
        "filename": "test_image.png",
        "content_type": "image/png",
        "type": "slider",
        "order": 1
    }


@pytest.fixture(scope="function")
def mock_server():
    """Мок сервера для тестов"""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post, \
         patch('requests.put') as mock_put, \
         patch('requests.delete') as mock_delete:
        
        # Настраиваем моки
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {}
        mock_get.return_value.text = "OK"
        
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"success": True}
        
        mock_put.return_value.status_code = 200
        mock_put.return_value.json.return_value = {"success": True}
        
        mock_delete.return_value.status_code = 200
        mock_delete.return_value.json.return_value = {"success": True}
        
        yield {
            "get": mock_get,
            "post": mock_post,
            "put": mock_put,
            "delete": mock_delete
        }


@pytest.fixture(scope="function")
def authenticated_session(test_session, test_base_url):
    """Аутентифицированная сессия для тестов"""
    # Попытка аутентификации
    login_data = {
        "email": "admin@example.com",
        "password": "adminpassword123"
    }
    
    try:
        response = test_session.post(
            f"{test_base_url}/login",
            data=login_data,
            timeout=10
        )
        
        if response.status_code == 200 and "cms" in response.url.lower():
            yield test_session
        else:
            # Если нет админа, создаем тестового пользователя
            registration_data = {
                "email": f"test_{pytest.current_test_id()}@example.com",
                "password": "testpassword123",
                "confirm_password": "testpassword123"
            }
            
            response = test_session.post(
                f"{test_base_url}/register",
                data=registration_data,
                timeout=10
            )
            
            if response.status_code == 200:
                yield test_session
            else:
                pytest.skip("Не удалось аутентифицироваться")
    except Exception:
        pytest.skip("Сервер недоступен")


@pytest.fixture(scope="function")
def test_directories():
    """Создание тестовых директорий"""
    test_dirs = [
        "tests/tmp",
        "tests/data",
        "tests/logs",
        "tests/reports"
    ]
    
    for dir_path in test_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    yield test_dirs
    
    # Очистка после тестов
    import shutil
    for dir_path in test_dirs:
        if Path(dir_path).exists():
            shutil.rmtree(dir_path, ignore_errors=True)


@pytest.fixture(scope="function")
def performance_timer():
    """Таймер для измерения производительности"""
    import time
    
    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return PerformanceTimer()


@pytest.fixture(scope="function")
def validation_test_cases():
    """Тестовые случаи для валидации"""
    return {
        "valid_emails": [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org"
        ],
        "invalid_emails": [
            "",
            "invalid",
            "@example.com",
            "test@",
            "test@.com"
        ],
        "valid_passwords": [
            "password123",
            "MySecure123",
            "12345678"
        ],
        "invalid_passwords": [
            "",
            "1234567",  # Слишком короткий
            "password",  # Только буквы
            "12345678"   # Только цифры
        ],
        "valid_texts": [
            "Hello World",
            "Текст с кириллицей",
            "A" * 1000  # Максимальная длина
        ],
        "invalid_texts": [
            "A" * 10001,  # Слишком длинный
            None,
            ""
        ]
    }


@pytest.fixture(scope="function")
def security_test_cases():
    """Тестовые случаи для безопасности"""
    return {
        "sql_injections": [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "1' UNION SELECT * FROM users--"
        ],
        "xss_attacks": [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<iframe src=javascript:alert('xss')></iframe>"
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "/etc/passwd",
            "C:\\Windows\\System32"
        ],
        "dangerous_filenames": [
            "malicious.exe",
            "script.js",
            "virus.bat",
            "backdoor.php"
        ]
    }


# Автоматические маркеры на основе имен файлов
def pytest_collection_modifyitems(config, items):
    """Автоматически добавляет маркеры на основе имен файлов"""
    for item in items:
        # Маркеры на основе пути к файлу
        if "unit_tests" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration_tests" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Маркеры на основе имени файла
        if "test_auth" in str(item.fspath):
            item.add_marker(pytest.mark.auth)
        elif "test_crud" in str(item.fspath):
            item.add_marker(pytest.mark.crud)
        elif "test_security" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        elif "test_performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "test_lighthouse" in str(item.fspath):
            item.add_marker(pytest.mark.lighthouse)
        
        # Маркеры на основе имени функции
        if "test_slow" in item.name:
            item.add_marker(pytest.mark.slow)
        if "test_network" in item.name:
            item.add_marker(pytest.mark.network)
        if "test_database" in item.name:
            item.add_marker(pytest.mark.database)


# Настройки для логирования
def pytest_configure(config):
    """Настройка pytest"""
    # Создаем директории для логов и отчетов
    os.makedirs("tests/logs", exist_ok=True)
    os.makedirs("tests/reports", exist_ok=True)
    os.makedirs("tests/tmp", exist_ok=True)


def pytest_sessionstart(session):
    """Начало сессии тестирования"""
    print("\n🧪 Начало тестирования CMS...")
    print("=" * 60)


def pytest_sessionfinish(session, exitstatus):
    """Завершение сессии тестирования"""
    print("\n" + "=" * 60)
    if exitstatus == 0:
        print("✅ Все тесты завершены успешно!")
    else:
        print(f"❌ Тесты завершены с ошибками (код: {exitstatus})")
    print("=" * 60)


# Настройки для покрытия кода
def pytest_runtest_setup(item):
    """Настройка перед каждым тестом"""
    # Очищаем кэш перед каждым тестом
    if hasattr(item, 'fixturenames') and 'test_cache' in item.fixturenames:
        pass  # Кэш будет очищен фикстурой


def pytest_runtest_teardown(item, nextitem):
    """Очистка после каждого теста"""
    # Очищаем временные файлы
    import tempfile
    tempfile.tempdir = "tests/tmp"
