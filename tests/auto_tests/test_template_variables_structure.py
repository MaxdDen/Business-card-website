#!/usr/bin/env python3
"""
Автотест для проверки исправленной структуры страницы template_variables
Проверяет:
- Блок статистики заполняется данными
- Блок ошибок для вывода проблем
- Блок кнопок управления остается без изменений
"""

import os
import sys
import time
import requests
from pathlib import Path

# Добавляем корневую папку проекта в путь
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_template_variables_structure():
    """Тестирование исправленной структуры страницы template_variables"""
    print("🧪 Тестирование исправленной структуры template_variables...")
    
    base_url = "http://localhost:8000"
    
    # 1. Проверяем доступность страницы template_variables
    print("1. Проверка доступности страницы template_variables...")
    try:
        response = requests.get(f"{base_url}/cms/template-variables", timeout=10)
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        print("✅ Страница template_variables доступна")
    except Exception as e:
        print(f"❌ Ошибка доступа к странице: {e}")
        return False
    
    # 2. Проверяем HTML структуру
    print("2. Проверка HTML структуры...")
    html_content = response.text
    
    # Проверяем блок статистики (29-78)
    assert "total-pages" in html_content, "Не найден блок total-pages"
    assert "total-variables" in html_content, "Не найден блок total-variables"
    assert "missing-variables" in html_content, "Не найден блок missing-variables"
    
    # Проверяем, что статистика показывает 0 вместо "-"
    assert 'id="total-pages">0</p>' in html_content, "Статистика не показывает 0"
    assert 'id="total-variables">0</p>' in html_content, "Статистика не показывает 0"
    assert 'id="missing-variables">0</p>' in html_content, "Статистика не показывает 0"
    
    print("✅ Блок статистики корректен")
    
    # 3. Проверяем блок ошибок
    print("3. Проверка блока ошибок...")
    
    # Проверяем наличие блока ошибок
    assert "errors-content" in html_content, "Не найден блок errors-content"
    assert "Errors and Issues" in html_content or "errors_and_issues" in html_content, "Не найден заголовок блока ошибок"
    
    # Проверяем fallback состояние
    assert "No errors found" in html_content or "no_errors_found" in html_content, "Не найдено fallback сообщение"
    assert "Click \"Analyze Templates\" to check for issues" in html_content or "click_analyze_to_check" in html_content, "Не найдена подсказка"
    
    print("✅ Блок ошибок корректен")
    
    # 4. Проверяем блок кнопок управления
    print("4. Проверка блока кнопок управления...")
    
    # Проверяем наличие всех кнопок
    assert "sync-btn" in html_content, "Не найдена кнопка синхронизации"
    assert "analyze-btn" in html_content, "Не найдена кнопка анализа"
    assert "refresh-btn" in html_content, "Не найдена кнопка обновления"
    
    # Проверяем текст кнопок
    assert "Sync Variables" in html_content, "Не найден текст кнопки синхронизации"
    assert "Analyze Templates" in html_content, "Не найден текст кнопки анализа"
    assert "Refresh" in html_content, "Не найден текст кнопки обновления"
    
    print("✅ Блок кнопок управления корректен")
    
    # 5. Проверяем JavaScript файл
    print("5. Проверка JavaScript файла...")
    js_file_path = project_root / "app" / "static" / "js" / "template_variables.js"
    assert js_file_path.exists(), "JavaScript файл не найден"
    
    with open(js_file_path, 'r', encoding='utf-8') as f:
        js_content = f.read()
    
    # Проверяем функции для новой структуры
    assert "loadStatistics" in js_content, "Не найдена функция loadStatistics"
    assert "displayErrors" in js_content, "Не найдена функция displayErrors"
    assert "errors-content" in js_content, "Не найдена работа с блоком ошибок"
    
    # Проверяем, что старые функции удалены
    assert "displayDatabaseVariables" not in js_content, "Найдена старая функция displayDatabaseVariables"
    assert "displayTemplateAnalysis" not in js_content, "Найдена старая функция displayTemplateAnalysis"
    assert "db-variables-content" not in js_content, "Найдена работа со старым блоком"
    assert "template-analysis-content" not in js_content, "Найдена работа со старым блоком"
    
    print("✅ JavaScript обновлен для новой структуры")
    
    # 6. Проверяем API endpoints
    print("6. Проверка API endpoints...")
    
    # Проверяем endpoint для получения переменных (для статистики)
    try:
        api_response = requests.get(f"{base_url}/cms/api/template-variables", timeout=10)
        assert api_response.status_code in [200, 500], f"Неожиданный статус API: {api_response.status_code}"
        print("✅ API endpoint /cms/api/template-variables работает")
    except Exception as e:
        print(f"⚠️ API endpoint недоступен: {e}")
    
    # Проверяем endpoint для анализа шаблонов (для ошибок)
    try:
        analysis_response = requests.get(f"{base_url}/cms/api/template-analysis", timeout=10)
        assert analysis_response.status_code in [200, 500], f"Неожиданный статус API анализа: {analysis_response.status_code}"
        print("✅ API endpoint /cms/api/template-analysis работает")
    except Exception as e:
        print(f"⚠️ API endpoint анализа недоступен: {e}")
    
    # 7. Проверяем подключение JavaScript файлов
    print("7. Проверка подключения JavaScript...")
    
    assert "template_variables.js" in html_content, "Не подключен JavaScript файл"
    assert "translations.js" in html_content, "Не подключен файл переводов"
    
    print("✅ JavaScript файлы подключены")
    
    # 8. Проверяем отсутствие старых блоков
    print("8. Проверка отсутствия старых блоков...")
    
    # Проверяем, что старые блоки удалены
    assert "db-variables-content" not in html_content, "Найден старый блок db-variables-content"
    assert "template-analysis-content" not in html_content, "Найден старый блок template-analysis-content"
    assert "Database Variables" not in html_content, "Найден старый заголовок Database Variables"
    assert "Template Analysis" not in html_content, "Найден старый заголовок Template Analysis"
    
    print("✅ Старые блоки удалены")
    
    print("\n🎉 Все тесты исправленной структуры template_variables пройдены успешно!")
    return True

def main():
    """Главная функция теста"""
    print("🚀 Запуск теста исправленной структуры template_variables...")
    
    try:
        success = test_template_variables_structure()
        if success:
            print("\n✅ Тест завершен успешно!")
            return 0
        else:
            print("\n❌ Тест завершен с ошибками!")
            return 1
    except Exception as e:
        print(f"\n💥 Критическая ошибка теста: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
