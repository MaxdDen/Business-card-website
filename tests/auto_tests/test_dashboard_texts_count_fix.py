#!/usr/bin/env python3
"""
Автотест для проверки исправления подсчета текстовых переменных в dashboard
"""

import sys
import os
import logging
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.database.db import query_one, query_all, execute
from app.cms.routes import get_dashboard_stats

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_dashboard_texts_count_fix():
    """Тест исправления подсчета текстовых переменных в dashboard"""
    logger.info("=== Тест исправления подсчета текстовых переменных в dashboard ===")
    
    try:
        # 1. Проверяем текущую статистику
        logger.info("1. Получение текущей статистики dashboard...")
        stats = get_dashboard_stats()
        logger.info(f"Текущая статистика: {stats}")
        
        # 2. Проверяем количество записей в таблице texts (публичные шаблоны)
        logger.info("2. Проверка записей в таблице texts (публичные шаблоны)...")
        texts_total = query_one("SELECT COUNT(*) as count FROM texts")["count"]
        logger.info(f"Общее количество записей в таблице texts: {texts_total}")
        
        # 3. Проверяем количество уникальных текстовых переменных
        logger.info("3. Проверка уникальных текстовых переменных...")
        unique_texts = query_one("SELECT COUNT(DISTINCT page || '.' || key) as count FROM texts")["count"]
        logger.info(f"Количество уникальных текстовых переменных: {unique_texts}")
        
        # 4. Проверяем количество записей в таблице texts_crm (системные переводы)
        logger.info("4. Проверка записей в таблице texts_crm (системные переводы)...")
        texts_crm_total = query_one("SELECT COUNT(*) as count FROM texts_crm")["count"]
        logger.info(f"Общее количество записей в таблице texts_crm: {texts_crm_total}")
        
        # 5. Проверяем структуру данных в таблице texts
        logger.info("5. Анализ структуры данных в таблице texts...")
        texts_structure = query_all("""
            SELECT page, key, COUNT(*) as count 
            FROM texts 
            GROUP BY page, key 
            ORDER BY page, key
        """)
        
        logger.info("Структура текстовых переменных:")
        for row in texts_structure:
            logger.info(f"  {row['page']}.{row['key']}: {row['count']} языков")
        
        # 6. Проверяем языки в таблице texts
        logger.info("6. Проверка языков в таблице texts...")
        languages_in_texts = query_all("SELECT DISTINCT lang FROM texts ORDER BY lang")
        logger.info(f"Языки в таблице texts: {[lang['lang'] for lang in languages_in_texts]}")
        
        # 7. Проверяем соответствие статистики
        logger.info("7. Проверка соответствия статистики...")
        
        # Проверяем, что texts_count теперь показывает количество уникальных переменных
        if stats['texts_count'] == unique_texts:
            logger.info("✅ texts_count корректно показывает количество уникальных текстовых переменных")
        else:
            logger.error(f"❌ texts_count не соответствует количеству уникальных переменных: {stats['texts_count']} != {unique_texts}")
            return False
        
        # Проверяем, что texts_count НЕ равен количеству записей в texts_crm
        if stats['texts_count'] != texts_crm_total:
            logger.info("✅ texts_count больше не показывает количество записей в texts_crm")
        else:
            logger.warning(f"⚠️ texts_count все еще равен количеству записей в texts_crm: {stats['texts_count']}")
        
        # Проверяем языки
        if stats['languages_count'] == len(languages_in_texts):
            logger.info("✅ languages_count корректно показывает количество языков из таблицы texts")
        else:
            logger.error(f"❌ languages_count не соответствует количеству языков: {stats['languages_count']} != {len(languages_in_texts)}")
            return False
        
        # 8. Проверяем, что статистика не пустая
        logger.info("8. Проверка непустоты статистики...")
        if stats['texts_count'] > 0:
            logger.info("✅ texts_count больше нуля - есть текстовые переменные")
        else:
            logger.warning("⚠️ texts_count равен нулю - возможно, нет текстовых переменных в публичных шаблонах")
        
        if stats['languages_count'] > 0:
            logger.info("✅ languages_count больше нуля - есть языки")
        else:
            logger.warning("⚠️ languages_count равен нулю - возможно, нет языков в таблице texts")
        
        logger.info("=== Тест исправления подсчета текстовых переменных завершен успешно ===")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка в тесте: {e}")
        return False


def test_dashboard_stats_structure():
    """Тест структуры статистики dashboard"""
    logger.info("=== Тест структуры статистики dashboard ===")
    
    try:
        stats = get_dashboard_stats()
        
        # Проверяем наличие всех необходимых полей
        required_fields = ['images_count', 'languages_count', 'active_languages', 'texts_count', 'users_count']
        
        for field in required_fields:
            if field in stats:
                logger.info(f"✅ Поле {field} присутствует: {stats[field]}")
            else:
                logger.error(f"❌ Поле {field} отсутствует")
                return False
        
        # Проверяем типы данных
        if isinstance(stats['images_count'], int):
            logger.info("✅ images_count имеет тип int")
        else:
            logger.error(f"❌ images_count имеет неправильный тип: {type(stats['images_count'])}")
            return False
        
        if isinstance(stats['languages_count'], int):
            logger.info("✅ languages_count имеет тип int")
        else:
            logger.error(f"❌ languages_count имеет неправильный тип: {type(stats['languages_count'])}")
            return False
        
        if isinstance(stats['texts_count'], int):
            logger.info("✅ texts_count имеет тип int")
        else:
            logger.error(f"❌ texts_count имеет неправильный тип: {type(stats['texts_count'])}")
            return False
        
        if isinstance(stats['users_count'], int):
            logger.info("✅ users_count имеет тип int")
        else:
            logger.error(f"❌ users_count имеет неправильный тип: {type(stats['users_count'])}")
            return False
        
        if isinstance(stats['active_languages'], list):
            logger.info("✅ active_languages имеет тип list")
        else:
            logger.error(f"❌ active_languages имеет неправильный тип: {type(stats['active_languages'])}")
            return False
        
        logger.info("=== Тест структуры статистики завершен успешно ===")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка в тесте структуры: {e}")
        return False


if __name__ == "__main__":
    logger.info("Запуск автотестов для исправления подсчета текстовых переменных в dashboard")
    
    success = True
    
    # Запускаем тесты
    if not test_dashboard_texts_count_fix():
        success = False
    
    if not test_dashboard_stats_structure():
        success = False
    
    if success:
        logger.info("🎉 Все тесты прошли успешно!")
        sys.exit(0)
    else:
        logger.error("💥 Некоторые тесты не прошли!")
        sys.exit(1)
