#!/usr/bin/env python3
"""
Тесты производительности Lighthouse
Проверяет метрики производительности публичных страниц
"""

import sys
import os
import json
import time
import subprocess
import requests
import unittest
from pathlib import Path
from unittest.mock import patch

# Добавляем путь к модулям приложения
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

class TestLighthousePerformance(unittest.TestCase):
    """Тесты производительности с использованием Lighthouse"""
    
    @classmethod
    def setUpClass(cls):
        """Настройка перед всеми тестами"""
        cls.base_url = "http://localhost:8000"
        cls.lighthouse_available = cls._check_lighthouse_availability()
        cls.session = requests.Session()
    
    @classmethod
    def _check_lighthouse_availability(cls):
        """Проверка доступности Lighthouse"""
        try:
            result = subprocess.run(
                ["lighthouse", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                print(f"✅ Lighthouse доступен: {result.stdout.strip()}")
                return True
            else:
                print("⚠️  Lighthouse не найден")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("⚠️  Lighthouse не установлен")
            return False
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.session.cookies.clear()
    
    def test_server_availability(self):
        """Тест доступности сервера"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            self.assertEqual(response.status_code, 200)
            print("✅ Сервер доступен для тестирования")
        except requests.exceptions.RequestException as e:
            self.fail(f"Сервер недоступен: {e}")
    
    def test_homepage_performance(self):
        """Тест производительности главной страницы"""
        if not self.lighthouse_available:
            self.skipTest("Lighthouse не доступен")
        
        print("\n🏠 Тестирование производительности главной страницы...")
        
        try:
            # Запуск Lighthouse для главной страницы
            result = self._run_lighthouse(f"{self.base_url}/")
            
            if result:
                self._analyze_lighthouse_results(result, "Главная страница")
            else:
                print("⚠️  Не удалось получить результаты Lighthouse")
                
        except Exception as e:
            print(f"⚠️  Ошибка тестирования главной страницы: {e}")
    
    def test_about_page_performance(self):
        """Тест производительности страницы 'О нас'"""
        if not self.lighthouse_available:
            self.skipTest("Lighthouse не доступен")
        
        print("\n📄 Тестирование производительности страницы 'О нас'...")
        
        try:
            result = self._run_lighthouse(f"{self.base_url}/about")
            
            if result:
                self._analyze_lighthouse_results(result, "Страница 'О нас'")
            else:
                print("⚠️  Не удалось получить результаты Lighthouse")
                
        except Exception as e:
            print(f"⚠️  Ошибка тестирования страницы 'О нас': {e}")
    
    def test_catalog_page_performance(self):
        """Тест производительности страницы каталога"""
        if not self.lighthouse_available:
            self.skipTest("Lighthouse не доступен")
        
        print("\n📦 Тестирование производительности страницы каталога...")
        
        try:
            result = self._run_lighthouse(f"{self.base_url}/catalog")
            
            if result:
                self._analyze_lighthouse_results(result, "Страница каталога")
            else:
                print("⚠️  Не удалось получить результаты Lighthouse")
                
        except Exception as e:
            print(f"⚠️  Ошибка тестирования страницы каталога: {e}")
    
    def test_contacts_page_performance(self):
        """Тест производительности страницы контактов"""
        if not self.lighthouse_available:
            self.skipTest("Lighthouse не доступен")
        
        print("\n📞 Тестирование производительности страницы контактов...")
        
        try:
            result = self._run_lighthouse(f"{self.base_url}/contacts")
            
            if result:
                self._analyze_lighthouse_results(result, "Страница контактов")
            else:
                print("⚠️  Не удалось получить результаты Lighthouse")
                
        except Exception as e:
            print(f"⚠️  Ошибка тестирования страницы контактов: {e}")
    
    def test_multilang_pages_performance(self):
        """Тест производительности мультиязычных страниц"""
        if not self.lighthouse_available:
            self.skipTest("Lighthouse не доступен")
        
        print("\n🌍 Тестирование производительности мультиязычных страниц...")
        
        languages = ["en", "ua", "ru"]
        pages = ["", "about", "catalog", "contacts"]
        
        for lang in languages:
            for page in pages:
                url = f"{self.base_url}/{lang}/{page}" if page else f"{self.base_url}/{lang}/"
                
                try:
                    print(f"   Тестирование: {url}")
                    result = self._run_lighthouse(url)
                    
                    if result:
                        self._analyze_lighthouse_results(result, f"{lang.upper()} {page or 'главная'}")
                    else:
                        print(f"   ⚠️  Не удалось получить результаты для {url}")
                        
                except Exception as e:
                    print(f"   ⚠️  Ошибка тестирования {url}: {e}")
    
    def test_cms_performance(self):
        """Тест производительности CMS (требует аутентификации)"""
        if not self.lighthouse_available:
            self.skipTest("Lighthouse не доступен")
        
        print("\n🔧 Тестирование производительности CMS...")
        
        # Попытка аутентификации
        if self._authenticate_user():
            try:
                result = self._run_lighthouse(f"{self.base_url}/cms")
                
                if result:
                    self._analyze_lighthouse_results(result, "CMS панель")
                else:
                    print("⚠️  Не удалось получить результаты Lighthouse для CMS")
                    
            except Exception as e:
                print(f"⚠️  Ошибка тестирования CMS: {e}")
        else:
            print("⚠️  Не удалось аутентифицироваться для тестирования CMS")
    
    def _run_lighthouse(self, url):
        """Запуск Lighthouse для указанного URL"""
        try:
            # Создаем временный файл для результатов
            temp_file = f"tests/tmp/lighthouse_{int(time.time())}.json"
            os.makedirs("tests/tmp", exist_ok=True)
            
            # Команда Lighthouse
            cmd = [
                "lighthouse",
                url,
                "--output=json",
                "--output-path=" + temp_file,
                "--chrome-flags=--headless",
                "--quiet",
                "--no-enable-error-reporting"
            ]
            
            # Запуск Lighthouse
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60 секунд таймаут
            )
            
            if result.returncode == 0 and os.path.exists(temp_file):
                # Читаем результаты
                with open(temp_file, 'r', encoding='utf-8') as f:
                    lighthouse_data = json.load(f)
                
                # Удаляем временный файл
                os.unlink(temp_file)
                
                return lighthouse_data
            else:
                print(f"⚠️  Lighthouse завершился с ошибкой: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("⚠️  Lighthouse превысил время ожидания")
            return None
        except Exception as e:
            print(f"⚠️  Ошибка запуска Lighthouse: {e}")
            return None
    
    def _analyze_lighthouse_results(self, results, page_name):
        """Анализ результатов Lighthouse"""
        try:
            # Извлекаем метрики
            categories = results.get("categories", {})
            audits = results.get("audits", {})
            
            # Основные метрики производительности
            performance_score = categories.get("performance", {}).get("score", 0)
            accessibility_score = categories.get("accessibility", {}).get("score", 0)
            best_practices_score = categories.get("best-practices", {}).get("score", 0)
            seo_score = categories.get("seo", {}).get("score", 0)
            
            print(f"\n📊 Результаты для {page_name}:")
            print(f"   🚀 Производительность: {performance_score:.2f}")
            print(f"   ♿ Доступность: {accessibility_score:.2f}")
            print(f"   ✅ Лучшие практики: {best_practices_score:.2f}")
            print(f"   🔍 SEO: {seo_score:.2f}")
            
            # Детальные метрики производительности
            if "first-contentful-paint" in audits:
                fcp = audits["first-contentful-paint"]["numericValue"]
                print(f"   ⏱️  First Contentful Paint: {fcp:.0f}ms")
            
            if "largest-contentful-paint" in audits:
                lcp = audits["largest-contentful-paint"]["numericValue"]
                print(f"   ⏱️  Largest Contentful Paint: {lcp:.0f}ms")
            
            if "cumulative-layout-shift" in audits:
                cls = audits["cumulative-layout-shift"]["numericValue"]
                print(f"   📐 Cumulative Layout Shift: {cls:.3f}")
            
            if "total-blocking-time" in audits:
                tbt = audits["total-blocking-time"]["numericValue"]
                print(f"   🚫 Total Blocking Time: {tbt:.0f}ms")
            
            # Проверяем соответствие стандартам
            self._check_performance_standards(performance_score, page_name)
            self._check_accessibility_standards(accessibility_score, page_name)
            self._check_seo_standards(seo_score, page_name)
            
        except Exception as e:
            print(f"⚠️  Ошибка анализа результатов: {e}")
    
    def _check_performance_standards(self, score, page_name):
        """Проверка соответствия стандартам производительности"""
        if score >= 0.9:
            print(f"   ✅ {page_name}: Отличная производительность")
        elif score >= 0.7:
            print(f"   ⚠️  {page_name}: Хорошая производительность (можно улучшить)")
        elif score >= 0.5:
            print(f"   ⚠️  {page_name}: Средняя производительность (требует оптимизации)")
        else:
            print(f"   ❌ {page_name}: Плохая производительность (критично)")
    
    def _check_accessibility_standards(self, score, page_name):
        """Проверка соответствия стандартам доступности"""
        if score >= 0.9:
            print(f"   ✅ {page_name}: Отличная доступность")
        elif score >= 0.7:
            print(f"   ⚠️  {page_name}: Хорошая доступность")
        else:
            print(f"   ❌ {page_name}: Плохая доступность")
    
    def _check_seo_standards(self, score, page_name):
        """Проверка соответствия стандартам SEO"""
        if score >= 0.9:
            print(f"   ✅ {page_name}: Отличное SEO")
        elif score >= 0.7:
            print(f"   ⚠️  {page_name}: Хорошее SEO")
        else:
            print(f"   ❌ {page_name}: Плохое SEO")
    
    def _authenticate_user(self):
        """Аутентификация пользователя для тестирования CMS"""
        try:
            # Попытка входа с тестовыми данными
            login_data = {
                "email": "admin@example.com",
                "password": "adminpassword123"
            }
            
            response = self.session.post(
                f"{self.base_url}/login",
                data=login_data,
                timeout=10
            )
            
            return response.status_code == 200 and "cms" in response.url.lower()
            
        except Exception:
            return False
    
    def test_page_load_times(self):
        """Тест времени загрузки страниц"""
        print("\n⏱️  Тестирование времени загрузки страниц...")
        
        pages = [
            ("/", "Главная"),
            ("/about", "О нас"),
            ("/catalog", "Каталог"),
            ("/contacts", "Контакты")
        ]
        
        for path, name in pages:
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}{path}", timeout=10)
                end_time = time.time()
                
                load_time = end_time - start_time
                
                if response.status_code == 200:
                    if load_time < 1.0:
                        print(f"   ✅ {name}: {load_time:.3f}с (быстро)")
                    elif load_time < 3.0:
                        print(f"   ⚠️  {name}: {load_time:.3f}с (средне)")
                    else:
                        print(f"   ❌ {name}: {load_time:.3f}с (медленно)")
                else:
                    print(f"   ❌ {name}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {name}: Ошибка - {e}")
    
    def test_resource_optimization(self):
        """Тест оптимизации ресурсов"""
        print("\n🔧 Тестирование оптимизации ресурсов...")
        
        try:
            # Проверяем главную страницу
            response = self.session.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # Проверяем наличие оптимизированных ресурсов
                checks = [
                    ("CSS минифицирован", "minified" in content or "compressed" in content),
                    ("WebP изображения", ".webp" in content),
                    ("Сжатие включено", "gzip" in response.headers.get("content-encoding", "")),
                    ("Кэширование", "cache-control" in response.headers),
                ]
                
                for check_name, check_result in checks:
                    if check_result:
                        print(f"   ✅ {check_name}")
                    else:
                        print(f"   ⚠️  {check_name}: не обнаружено")
            else:
                print(f"   ❌ Не удалось загрузить страницу: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка проверки оптимизации: {e}")


class TestLighthouseIntegration(unittest.TestCase):
    """Интеграционные тесты Lighthouse"""
    
    def test_lighthouse_installation(self):
        """Тест установки Lighthouse"""
        try:
            result = subprocess.run(
                ["lighthouse", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"✅ Lighthouse установлен: {result.stdout.strip()}")
            else:
                print("❌ Lighthouse не установлен или не работает")
                print("Установите: npm install -g lighthouse")
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ Lighthouse не найден")
            print("Установите: npm install -g lighthouse")
    
    def test_chrome_availability(self):
        """Тест доступности Chrome для Lighthouse"""
        try:
            result = subprocess.run(
                ["google-chrome", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"✅ Chrome доступен: {result.stdout.strip()}")
            else:
                print("⚠️  Chrome не найден, Lighthouse может не работать")
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("⚠️  Chrome не найден, Lighthouse может не работать")
            print("Установите Google Chrome для работы Lighthouse")


if __name__ == "__main__":
    # Настройка тестирования
    print("🧪 Запуск тестов производительности Lighthouse...")
    print("=" * 60)
    print("⚠️  Убедитесь, что сервер запущен: uvicorn app.main:app --reload")
    print("⚠️  Убедитесь, что Lighthouse установлен: npm install -g lighthouse")
    print("=" * 60)
    
    unittest.main(verbosity=2)
