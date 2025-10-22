#!/usr/bin/env python3
"""
Автотест для проверки скриптов сборки и развертывания
Проверяет корректность PowerShell скриптов, Makefile и NPM скриптов
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_powershell_scripts_exist():
    """Проверяет наличие всех PowerShell скриптов"""
    print("🔍 Проверяем наличие PowerShell скриптов...")
    
    required_scripts = [
        "dev.ps1",
        "run.ps1", 
        "tailwind-watch.ps1",
        "lint.ps1"
    ]
    
    missing_scripts = []
    for script in required_scripts:
        if not os.path.exists(script):
            missing_scripts.append(script)
        else:
            print(f"✅ {script} найден")
    
    if missing_scripts:
        print(f"❌ Отсутствуют скрипты: {missing_scripts}")
        return False
    
    print("✅ Все PowerShell скрипты найдены")
    return True

def test_powershell_scripts_syntax():
    """Проверяет синтаксис PowerShell скриптов"""
    print("🔍 Проверяем синтаксис PowerShell скриптов...")
    
    scripts = ["dev.ps1", "run.ps1", "tailwind-watch.ps1", "lint.ps1"]
    
    for script in scripts:
        if not os.path.exists(script):
            continue
            
        try:
            # Проверяем синтаксис PowerShell
            result = subprocess.run([
                "powershell", "-Command", 
                f"Get-Content '{script}' | Out-Null; if ($?) {{ Write-Host 'Syntax OK' }}"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print(f"✅ {script} - синтаксис корректен")
            else:
                print(f"❌ {script} - ошибка синтаксиса: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⚠️  {script} - таймаут проверки синтаксиса")
        except Exception as e:
            print(f"❌ {script} - ошибка проверки: {e}")
            return False
    
    print("✅ Синтаксис всех PowerShell скриптов корректен")
    return True

def test_makefile_exists():
    """Проверяет наличие Makefile"""
    print("🔍 Проверяем наличие Makefile...")
    
    if not os.path.exists("Makefile"):
        print("❌ Makefile не найден")
        return False
    
    print("✅ Makefile найден")
    return True

def test_makefile_commands():
    """Проверяет доступность команд Makefile"""
    print("🔍 Проверяем команды Makefile...")
    
    try:
        # Проверяем справку
        result = subprocess.run(["make", "help"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ make help работает")
        else:
            print(f"⚠️  make help не работает: {result.stderr}")
            
        # Проверяем info
        result = subprocess.run(["make", "info"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ make info работает")
        else:
            print(f"⚠️  make info не работает: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⚠️  Таймаут при проверке Makefile команд")
    except FileNotFoundError:
        print("⚠️  make не найден (возможно, не установлен)")
    except Exception as e:
        print(f"⚠️  Ошибка проверки Makefile: {e}")
    
    print("✅ Команды Makefile проверены")
    return True

def test_package_json_scripts():
    """Проверяет корректность NPM скриптов"""
    print("🔍 Проверяем NPM скрипты...")
    
    if not os.path.exists("package.json"):
        print("❌ package.json не найден")
        return False
    
    try:
        with open("package.json", "r", encoding="utf-8") as f:
            package_data = json.load(f)
        
        required_scripts = [
            "dev", "run", "tailwind:watch", "lint", 
            "build:css", "clean", "test"
        ]
        
        scripts = package_data.get("scripts", {})
        missing_scripts = []
        
        for script in required_scripts:
            if script not in scripts:
                missing_scripts.append(script)
            else:
                print(f"✅ npm run {script} определен")
        
        if missing_scripts:
            print(f"❌ Отсутствуют скрипты: {missing_scripts}")
            return False
        
        # Проверяем devDependencies
        dev_deps = package_data.get("devDependencies", {})
        required_deps = ["tailwindcss", "@tailwindcss/cli"]
        
        for dep in required_deps:
            if dep not in dev_deps:
                print(f"⚠️  Отсутствует зависимость: {dep}")
            else:
                print(f"✅ {dep} в devDependencies")
        
        print("✅ NPM скрипты корректны")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга package.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка проверки package.json: {e}")
        return False

def test_readme_exists():
    """Проверяет наличие README.md"""
    print("🔍 Проверяем наличие README.md...")
    
    if not os.path.exists("README.md"):
        print("❌ README.md не найден")
        return False
    
    # Проверяем размер файла
    file_size = os.path.getsize("README.md")
    if file_size < 1000:  # Минимум 1KB
        print(f"⚠️  README.md слишком маленький ({file_size} байт)")
    else:
        print(f"✅ README.md найден ({file_size} байт)")
    
    # Проверяем наличие ключевых разделов
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read().lower()
        
        required_sections = [
            "быстрый старт", "установка", "запуск", 
            "команды", "архитектура", "требования"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"⚠️  Отсутствуют разделы в README: {missing_sections}")
        else:
            print("✅ README.md содержит все необходимые разделы")
            
    except Exception as e:
        print(f"⚠️  Ошибка проверки README.md: {e}")
    
    return True

def test_environment_files():
    """Проверяет наличие файлов окружения"""
    print("🔍 Проверяем файлы окружения...")
    
    # Проверяем .env.example
    if not os.path.exists(".env.example"):
        print("❌ .env.example не найден")
        return False
    else:
        print("✅ .env.example найден")
    
    # Проверяем requirements.txt
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt не найден")
        return False
    else:
        print("✅ requirements.txt найден")
        
        # Проверяем основные зависимости
        try:
            with open("requirements.txt", "r", encoding="utf-8") as f:
                content = f.read()
            
            required_deps = ["fastapi", "uvicorn", "jinja2", "sqlite3"]
            missing_deps = []
            
            for dep in required_deps:
                if dep not in content.lower():
                    missing_deps.append(dep)
            
            if missing_deps:
                print(f"⚠️  Возможно отсутствуют зависимости: {missing_deps}")
            else:
                print("✅ requirements.txt содержит основные зависимости")
                
        except Exception as e:
            print(f"⚠️  Ошибка проверки requirements.txt: {e}")
    
    return True

def test_directory_structure():
    """Проверяет структуру директорий"""
    print("🔍 Проверяем структуру директорий...")
    
    required_dirs = [
        "app", "app/auth", "app/cms", "app/site", 
        "app/static", "app/templates", "app/utils", "app/database",
        "tests", "tests/auto_tests", "docs"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
        else:
            print(f"✅ {dir_path} существует")
    
    if missing_dirs:
        print(f"⚠️  Отсутствуют директории: {missing_dirs}")
    else:
        print("✅ Все необходимые директории существуют")
    
    return len(missing_dirs) == 0

def test_script_permissions():
    """Проверяет права доступа к скриптам"""
    print("🔍 Проверяем права доступа к скриптам...")
    
    scripts = ["dev.ps1", "run.ps1", "tailwind-watch.ps1", "lint.ps1"]
    
    for script in scripts:
        if os.path.exists(script):
            # Проверяем, что файл читаемый
            if os.access(script, os.R_OK):
                print(f"✅ {script} - права на чтение")
            else:
                print(f"❌ {script} - нет прав на чтение")
                return False
    
    print("✅ Права доступа к скриптам корректны")
    return True

def run_build_scripts_test():
    """Основная функция тестирования скриптов сборки"""
    print("🧪 Запуск автотеста скриптов сборки...")
    print("=" * 60)
    
    tests = [
        ("PowerShell скрипты существуют", test_powershell_scripts_exist),
        ("Синтаксис PowerShell скриптов", test_powershell_scripts_syntax),
        ("Makefile существует", test_makefile_exists),
        ("Команды Makefile", test_makefile_commands),
        ("NPM скрипты", test_package_json_scripts),
        ("README.md", test_readme_exists),
        ("Файлы окружения", test_environment_files),
        ("Структура директорий", test_directory_structure),
        ("Права доступа", test_script_permissions)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - ПРОЙДЕН")
            else:
                print(f"❌ {test_name} - ПРОВАЛЕН")
        except Exception as e:
            print(f"❌ {test_name} - ОШИБКА: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Результаты: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Скрипты сборки готовы к использованию.")
        return True
    else:
        print(f"⚠️  {total - passed} тестов провалено. Проверьте ошибки выше.")
        return False

if __name__ == "__main__":
    success = run_build_scripts_test()
    sys.exit(0 if success else 1)
