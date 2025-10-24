#!/usr/bin/env python3
"""
Скрипт для корректного запуска сервера с обработкой зависших соединений
"""
import os
import sys
import signal
import subprocess
import time
import psutil
from pathlib import Path

def kill_existing_processes():
    """Завершить все существующие процессы Python/uvicorn"""
    print("🔍 Поиск и завершение существующих процессов...")
    
    killed_count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if 'uvicorn' in cmdline or 'app.main:app' in cmdline:
                    print(f"🔄 Завершение процесса PID {proc.info['pid']}: {cmdline}")
                    proc.kill()
                    killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    if killed_count > 0:
        print(f"✅ Завершено {killed_count} процессов")
        time.sleep(2)  # Дать время на завершение
    else:
        print("ℹ️  Активных процессов не найдено")

def create_env_file():
    """Создать файл .env если его нет"""
    env_file = Path('.env')
    env_example = Path('env.example')
    
    if not env_file.exists() and env_example.exists():
        print("📝 Создание файла .env из env.example...")
        with open(env_example, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Файл .env создан")
    elif env_file.exists():
        print("✅ Файл .env уже существует")
    else:
        print("⚠️  Файл env.example не найден")

def check_dependencies():
    """Проверить зависимости"""
    print("🔍 Проверка зависимостей...")
    
    try:
        import fastapi
        import uvicorn
        import jinja2
        print("✅ Основные зависимости установлены")
        return True
    except ImportError as e:
        print(f"❌ Отсутствует зависимость: {e}")
        print("💡 Запустите: pip install -r requirements.txt")
        return False

def start_server():
    """Запустить сервер с правильными параметрами"""
    print("🚀 Запуск сервера...")
    
    # Параметры для uvicorn
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', 8000))
    
    cmd = [
        sys.executable, '-m', 'uvicorn',
        'app.main:app',
        '--host', host,
        '--port', str(port),
        '--reload',
        '--log-level', 'info',
        '--access-log',
        '--timeout-keep-alive', '30',  # Таймаут для keep-alive соединений
        '--limit-concurrency', '100',  # Ограничение одновременных соединений
        '--limit-max-requests', '1000'  # Ограничение запросов на worker
    ]
    
    print(f"🌐 Сервер будет доступен по адресу: http://{host}:{port}")
    print("🔄 Для остановки нажмите Ctrl+C")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен пользователем")
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка запуска сервера: {e}")
        return False
    
    return True

def main():
    """Основная функция"""
    print("🚀 Запуск CMS сервера с исправлением зависших соединений")
    print("=" * 60)
    
    # Проверка рабочей директории
    if not Path('app/main.py').exists():
        print("❌ Запустите скрипт из корневой директории проекта")
        sys.exit(1)
    
    # Создание .env файла
    create_env_file()
    
    # Проверка зависимостей
    if not check_dependencies():
        sys.exit(1)
    
    # Завершение существующих процессов
    kill_existing_processes()
    
    # Запуск сервера
    start_server()

if __name__ == '__main__':
    main()
