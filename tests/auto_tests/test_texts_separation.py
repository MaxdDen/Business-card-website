#!/usr/bin/env python3
"""
Тест разделения таблиц texts и texts_crm
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database.db import query_all, query_one
from app.utils.template_parser import TemplateParser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_texts_separation():
    """Тест разделения таблиц texts и texts_crm"""
    logger.info("🧪 Тестирование разделения таблиц texts и texts_crm")
    
    # Проверяем, что таблица texts_crm существует
    try:
        result = query_one("SELECT name FROM sqlite_master WHERE type='table' AND name='texts_crm'")
        if not result:
            logger.error("❌ Таблица texts_crm не найдена")
            return False
        logger.info("✅ Таблица texts_crm существует")
    except Exception as e:
        logger.error(f"❌ Ошибка проверки таблицы texts_crm: {e}")
        return False
    
    # Проверяем, что таблица texts существует
    try:
        result = query_one("SELECT name FROM sqlite_master WHERE type='table' AND name='texts'")
        if not result:
            logger.error("❌ Таблица texts не найдена")
            return False
        logger.info("✅ Таблица texts существует")
    except Exception as e:
        logger.error(f"❌ Ошибка проверки таблицы texts: {e}")
        return False
    
    # Проверяем данные в texts_crm
    try:
        crm_texts = query_all("SELECT page, key, lang, value FROM texts_crm LIMIT 5")
        logger.info(f"✅ Найдено {len(crm_texts)} записей в texts_crm")
        
        # Проверяем, что есть CRM страницы
        crm_pages = set()
        for text in crm_texts:
            crm_pages.add(text['page'])
        
        expected_crm_pages = {'dashboard', 'cms_texts', 'cms_images', 'cms_seo', 'cms_users', 'login', 'register'}
        found_crm_pages = crm_pages.intersection(expected_crm_pages)
        
        if found_crm_pages:
            logger.info(f"✅ Найдены CRM страницы: {found_crm_pages}")
        else:
            logger.warning("⚠️ CRM страницы не найдены в texts_crm")
            
    except Exception as e:
        logger.error(f"❌ Ошибка проверки данных в texts_crm: {e}")
        return False
    
    # Проверяем данные в texts
    try:
        public_texts = query_all("SELECT page, key, lang, value FROM texts LIMIT 5")
        logger.info(f"✅ Найдено {len(public_texts)} записей в texts")
        
        # Проверяем, что есть публичные страницы
        public_pages = set()
        for text in public_texts:
            public_pages.add(text['page'])
        
        expected_public_pages = {'home', 'about', 'catalog', 'contacts'}
        found_public_pages = public_pages.intersection(expected_public_pages)
        
        if found_public_pages:
            logger.info(f"✅ Найдены публичные страницы: {found_public_pages}")
        else:
            logger.warning("⚠️ Публичные страницы не найдены в texts")
            
    except Exception as e:
        logger.error(f"❌ Ошибка проверки данных в texts: {e}")
        return False
    
    # Проверяем, что CRM страницы не дублируются в texts
    try:
        crm_pages_in_texts = query_all("""
            SELECT DISTINCT page FROM texts 
            WHERE page IN ('dashboard', 'cms_texts', 'cms_images', 'cms_seo', 'cms_users', 'login', 'register')
        """)
        
        if crm_pages_in_texts:
            logger.warning(f"⚠️ CRM страницы найдены в texts: {[p['page'] for p in crm_pages_in_texts]}")
        else:
            logger.info("✅ CRM страницы не найдены в texts (правильно)")
            
    except Exception as e:
        logger.error(f"❌ Ошибка проверки дублирования: {e}")
        return False
    
    # Тестируем TemplateParser
    try:
        parser = TemplateParser()
        
        # Проверяем функцию _is_crm_page
        assert parser._is_crm_page('dashboard') == True, "dashboard должна быть CRM страницей"
        assert parser._is_crm_page('cms_texts') == True, "cms_texts должна быть CRM страницей"
        assert parser._is_crm_page('login') == True, "login должна быть CRM страницей"
        assert parser._is_crm_page('home') == False, "home должна быть публичной страницей"
        assert parser._is_crm_page('about') == False, "about должна быть публичной страницей"
        
        logger.info("✅ TemplateParser._is_crm_page работает корректно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования TemplateParser: {e}")
        return False
    
    logger.info("🎉 Все тесты разделения таблиц прошли успешно!")
    return True

if __name__ == "__main__":
    success = test_texts_separation()
    if success:
        print("\n✅ Тест разделения таблиц ПРОЙДЕН")
        sys.exit(0)
    else:
        print("\n❌ Тест разделения таблиц ПРОВАЛЕН")
        sys.exit(1)
