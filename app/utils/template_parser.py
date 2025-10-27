"""
Парсер HTML шаблонов для автоматического извлечения переменных
"""
import re
import os
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from app.database.db import execute, query_one, query_all
from app.site.config import get_supported_languages

logger = logging.getLogger(__name__)


class TemplateParser:
    """Парсер HTML шаблонов для автоматического извлечения переменных"""
    
    def __init__(self, templates_dir: str = "app/templates"):
        self.templates_dir = Path(templates_dir)
        
        # Регулярные выражения для поиска переменных
        self.variable_pattern = re.compile(r'\{\{\s*([^}]+)\s*\}\}')
        self.conditional_pattern = re.compile(r'\{\%\s*if\s+([^%]+)\s*\%\}')
        
        # Поддерживаемые namespace'ы для парсинга
        self.supported_namespaces = {'texts', 'seo', 'images'}
        
        # Системные переменные, которые исключаем из парсинга
        self.system_variables = {
            'lang', 'request', 'supported_languages', 'language_urls',
            'loop.index', 'loop.first', 'loop.last', 'loop.length',
            'csrf_token', 'user_email', 'current_user', 'translations',
            'cms_url', 'get_cms_url'
        }
        
    def _is_crm_page(self, page: str) -> bool:
        """Определить, является ли страница CRM страницей"""
        crm_pages = {
            'dashboard', 'cms_texts', 'cms_images', 'cms_seo', 'cms_users', 
            'cms_template_variables', 'cms_dynamic_images', 'cms_dynamic_seo',
            'login', 'register'
        }
        return page in crm_pages
    
    @staticmethod
    def get_available_pages(templates_dir: str = "app/templates") -> List[str]:
        """
        Получает список доступных страниц из папки app/templates/public/
        
        Args:
            templates_dir: Путь к папке templates (по умолчанию "app/templates")
        
        Returns:
            Список названий страниц (без расширения .html)
        """
        try:
            public_templates_dir = Path(templates_dir) / "public"
            
            if not public_templates_dir.exists():
                logger.warning(f"Директория {public_templates_dir} не найдена")
                return []
            
            # Получаем все HTML файлы в папке public
            html_files = list(public_templates_dir.glob("*.html"))
            
            # Извлекаем названия страниц (без расширения)
            pages = []
            for html_file in html_files:
                page_name = html_file.stem  # Получаем имя файла без расширения
                pages.append(page_name)
            
            logger.debug(f"Найдены страницы: {sorted(pages)}")
            return sorted(pages)
            
        except Exception as e:
            logger.error(f"Ошибка получения списка страниц: {e}")
            return []
    
    def extract_variables_from_file(self, template_path: str) -> Set[str]:
        """
        Извлекает все переменные из одного шаблона
        
        Args:
            template_path: Путь к файлу шаблона
            
        Returns:
            Множество найденных переменных
        """
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            variables = set()
            
            # Ищем переменные в {{ }}
            for match in self.variable_pattern.findall(content):
                var_expression = match.strip()
                
                # Извлекаем все переменные из выражения (включая выражения с or)
                expression_vars = self._extract_variables_from_expression(var_expression)
                for var in expression_vars:
                    if self._is_parseable_variable(var):
                        variables.add(var)
            
            # Ищем переменные в условиях
            for match in self.conditional_pattern.findall(content):
                condition = match.strip()
                
                # Извлекаем все переменные из логического выражения
                condition_vars = self._extract_variables_from_condition(condition)
                for var in condition_vars:
                    if self._is_parseable_variable(var):
                        variables.add(var)
            
            logger.debug(f"Найдено {len(variables)} переменных в {template_path}: {variables}")
            return variables
            
        except Exception as e:
            logger.error(f"Ошибка парсинга шаблона {template_path}: {e}")
            return set()
    
    def _extract_variables_from_expression(self, expression: str) -> Set[str]:
        """
        Извлекает все переменные из выражения (включая выражения с or)
        
        Args:
            expression: Выражение (например: "images.slider1_alt or 'Slider image 1'")
            
        Returns:
            Множество найденных переменных
        """
        variables = set()
        
        try:
            # Очищаем от фильтров (|)
            if '|' in expression:
                expression = expression.split('|')[0].strip()
            
            # Разбиваем выражение по ' or '
            parts = expression.split(' or ')
            
            for part in parts:
                part = part.strip()
                
                # Очищаем от кавычек и лишних пробелов
                part = part.strip('\'"').strip()
                
                # Проверяем, что это переменная (содержит точку и не является строкой)
                if '.' in part and not part.startswith(('"', "'")):
                    # Проверяем, что это не функция (нет скобок)
                    if '(' not in part and ')' not in part:
                        variables.add(part)
            
            logger.debug(f"Извлечено {len(variables)} переменных из выражения '{expression}': {variables}")
            return variables
            
        except Exception as e:
            logger.error(f"Ошибка извлечения переменных из выражения '{expression}': {e}")
            return set()
    
    def _extract_variables_from_condition(self, condition: str) -> Set[str]:
        """
        Извлекает все переменные из логического выражения
        
        Args:
            condition: Логическое выражение (например: "images.slider1 or images.slider2")
            
        Returns:
            Множество найденных переменных
        """
        variables = set()
        
        try:
            # Разбиваем выражение по логическим операторам
            # Поддерживаем: or, and, ==, !=, in, not in
            operators = [' or ', ' and ', ' == ', ' != ', ' in ', ' not in ']
            
            # Заменяем операторы на разделители
            condition_copy = condition
            for op in operators:
                condition_copy = condition_copy.replace(op, '|SPLIT|')
            
            # Разбиваем по разделителям
            parts = condition_copy.split('|SPLIT|')
            
            for part in parts:
                part = part.strip()
                
                # Очищаем от скобок и лишних пробелов
                part = part.strip('()').strip()
                
                # Очищаем от кавычек
                part = part.strip('\'"').strip()
                
                # Проверяем, что это переменная (содержит точку и не является строкой)
                if '.' in part and not part.startswith(('"', "'")) and not part.startswith('loop.'):
                    # Проверяем, что это не функция (нет скобок)
                    if '(' not in part and ')' not in part:
                        variables.add(part)
            
            logger.debug(f"Извлечено {len(variables)} переменных из условия '{condition}': {variables}")
            return variables
            
        except Exception as e:
            logger.error(f"Ошибка извлечения переменных из условия '{condition}': {e}")
            return set()
    
    def _is_parseable_variable(self, variable: str) -> bool:
        """
        Проверяет, является ли переменная подходящей для парсинга
        
        Args:
            variable: Переменная для проверки
            
        Returns:
            True если переменная подходит для парсинга
        """
        # Исключаем системные переменные
        if variable in self.system_variables:
            return False
        
        # Исключаем переменные циклов
        if variable.startswith('loop.'):
            return False
        
        # Исключаем переменные без namespace
        if '.' not in variable:
            return False
        
        # Проверяем поддерживаемые namespace
        namespace = variable.split('.')[0]
        if namespace not in self.supported_namespaces:
            return False
        
        # Исключаем переменные с функциями
        if '(' in variable or ')' in variable:
            return False
        
        return True
    
    def get_page_from_path(self, template_path: str) -> str:
        """
        Определяет страницу по пути к шаблону (динамически)
        
        Args:
            template_path: Путь к файлу шаблона
            
        Returns:
            Название страницы
        """
        try:
            path = Path(template_path)
            
            # Ищем относительный путь от templates
            try:
                if self.templates_dir in path.parents:
                    relative_path = path.relative_to(self.templates_dir)
                    template_name = str(relative_path)
                else:
                    # Если шаблон не в templates_dir, ищем public/ в пути
                    path_str = str(path)
                    if 'public/' in path_str:
                        # Извлекаем имя файла из пути с public/
                        parts = path_str.split('public/')
                        if len(parts) > 1:
                            template_name = 'public/' + parts[1]
                        else:
                            template_name = path.name
                    else:
                        template_name = path.name
                
                # Нормализуем путь для кроссплатформенности
                template_name = template_name.replace('\\', '/')
                
                # Если это файл из папки public, извлекаем название страницы
                if template_name.startswith('public/') and template_name.endswith('.html'):
                    page_name = Path(template_name).stem
                    logger.debug(f"Определена страница {page_name} для {template_path}")
                    return page_name
                
            except ValueError:
                # Если не можем найти относительный путь, пробуем по имени файла
                page_name = path.stem
                logger.debug(f"Определена страница {page_name} для {template_path} (по имени файла)")
                return page_name
                
        except Exception as e:
            logger.error(f"Ошибка определения страницы для {template_path}: {e}")
            return 'unknown'
    
    def parse_all_templates(self) -> Dict[str, Set[str]]:
        """
        Парсит все шаблоны и возвращает переменные по страницам
        
        Returns:
            Словарь {страница: множество_переменных}
        """
        results = {}
        
        try:
            # Ищем все HTML файлы в public директории
            public_templates = self.templates_dir / "public"
            if not public_templates.exists():
                logger.warning(f"Директория {public_templates} не найдена")
                return results
            
            html_files = list(public_templates.glob("*.html"))
            logger.info(f"Найдено {len(html_files)} HTML файлов для парсинга")
            
            for template_file in html_files:
                page = self.get_page_from_path(str(template_file))
                variables = self.extract_variables_from_file(str(template_file))
                
                if variables:
                    results[page] = variables
                    logger.info(f"Найдено {len(variables)} переменных в {page}: {variables}")
                else:
                    logger.debug(f"Переменные не найдены в {page}")
            
            return results
            
        except Exception as e:
            logger.error(f"Ошибка парсинга всех шаблонов: {e}")
            return {}
    
    def sync_variables_to_database(self, supported_languages: List[str] = None) -> Dict[str, int]:
        """
        Синхронизирует найденные переменные с базой данных (только добавляет новые)
        
        Args:
            supported_languages: Список поддерживаемых языков
            
        Returns:
            Словарь с результатами синхронизации
        """
        if supported_languages is None:
            supported_languages = get_supported_languages()
        
        results = {
            'parsed_pages': 0,
            'added_variables': 0,
            'skipped_variables': 0,
            'errors': 0
        }
        
        try:
            # Парсим все шаблоны
            template_variables = self.parse_all_templates()
            results['parsed_pages'] = len(template_variables)
            
            logger.info(f"Начинаем синхронизацию {len(template_variables)} страниц")
            
            for page, variables in template_variables.items():
                if page == 'unknown':
                    logger.warning("Пропускаем страницу 'unknown'")
                    continue
                
                logger.info(f"Синхронизация страницы {page} с {len(variables)} переменными")
                
                # Специальная обработка для base.html как глобального шаблона
                if page == 'base':
                    self._sync_global_variables(variables, supported_languages, results)
                    continue
                
                # Группируем переменные по namespace
                texts_vars = set()
                seo_vars = set()
                images_vars = set()
                images_alt_vars = set()  # Новый набор для alt-атрибутов
                
                for variable in variables:
                    # Извлекаем namespace и ключ из переменной (texts.title -> texts, title)
                    if '.' in variable:
                        namespace = variable.split('.')[0]
                        key = variable.split('.', 1)[1]
                    else:
                        namespace = 'texts'  # fallback
                        key = variable
                    
                    # Группируем по namespace
                    if namespace == 'texts':
                        texts_vars.add(key)
                    elif namespace == 'seo':
                        seo_vars.add(key)
                    elif namespace == 'images':
                        # Проверяем, является ли это alt-атрибутом
                        if key.endswith('_alt'):
                            images_alt_vars.add(key)
                        else:
                            images_vars.add(key)
                    else:
                        logger.warning(f"Неподдерживаемый namespace: {namespace}")
                
                # Синхронизируем текстовые переменные
                for key in texts_vars:
                    self._sync_text_variable(page, key, supported_languages, results)
                
                # Синхронизируем SEO переменные (одна запись на страницу)
                if seo_vars:
                    self._sync_seo_variables(page, seo_vars, supported_languages, results)
                
                # Синхронизируем переменные изображений
                for key in images_vars:
                    self._sync_image_variable(page, key, supported_languages, results)
                
                # Синхронизируем alt-атрибуты изображений
                for key in images_alt_vars:
                    self._sync_image_alt_variable(page, key, supported_languages, results)
            
            logger.info(f"Синхронизация завершена: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка синхронизации переменных: {e}")
            results['errors'] += 1
            return results
    
    def _sync_text_variable(self, page: str, key: str, supported_languages: List[str], results: Dict[str, int]):
        """Синхронизация текстовой переменной"""
        # Определяем таблицу в зависимости от типа страницы
        table_name = "texts_crm" if self._is_crm_page(page) else "texts"
        
        for lang in supported_languages:
            try:
                # Проверяем, существует ли уже запись
                existing = query_one(
                    f"SELECT id FROM {table_name} WHERE page = ? AND key = ? AND lang = ?",
                    (page, key, lang)
                )
                
                if not existing:
                    # Добавляем новую переменную с пустым значением
                    execute(
                        f"INSERT INTO {table_name} (page, key, lang, value) VALUES (?, ?, ?, ?)",
                        (page, key, lang, "")
                    )
                    results['added_variables'] += 1
                    logger.debug(f"Добавлена текстовая переменная: {page}.{key}.{lang}")
                else:
                    results['skipped_variables'] += 1
                    logger.debug(f"Текстовая переменная уже существует: {page}.{key}.{lang}")
                    
            except Exception as e:
                results['errors'] += 1
                logger.error(f"Ошибка добавления текстовой переменной {page}.{key}.{lang}: {e}")
    
    def _sync_seo_variable(self, page: str, key: str, supported_languages: List[str], results: Dict[str, int]):
        """Синхронизация SEO переменной"""
        for lang in supported_languages:
            try:
                # Проверяем, существует ли уже запись
                existing = query_one(
                    "SELECT id FROM seo WHERE page = ? AND lang = ?",
                    (page, lang)
                )
                
                if not existing:
                    # Добавляем новую SEO запись с пустыми значениями
                    execute(
                        "INSERT INTO seo (page, lang, title, description, keywords) VALUES (?, ?, ?, ?, ?)",
                        (page, lang, "", "", "")
                    )
                    results['added_variables'] += 1
                    logger.debug(f"Добавлена SEO запись: {page}.{lang}")
                else:
                    results['skipped_variables'] += 1
                    logger.debug(f"SEO запись уже существует: {page}.{lang}")
                    
            except Exception as e:
                results['errors'] += 1
                logger.error(f"Ошибка добавления SEO записи {page}.{lang}: {e}")
    
    def _sync_seo_variables(self, page: str, template_keys: set, supported_languages: List[str], results: Dict[str, int]):
        """Синхронизация переменных SEO"""
        # Для SEO создаем одну запись на страницу и язык
        for lang in supported_languages:
            try:
                # Проверяем, существует ли уже запись
                existing = query_one(
                    "SELECT id FROM seo WHERE page = ? AND lang = ?",
                    (page, lang)
                )
                
                if not existing:
                    # Добавляем новую SEO запись с пустыми значениями
                    execute(
                        "INSERT INTO seo (page, lang, title, description, keywords) VALUES (?, ?, ?, ?, ?)",
                        (page, lang, "", "", "")
                    )
                    results['added_variables'] += 1
                    logger.debug(f"Добавлена SEO запись: {page}.{lang}")
                else:
                    results['skipped_variables'] += 1
                    logger.debug(f"SEO запись уже существует: {page}.{lang}")
                    
            except Exception as e:
                results['errors'] += 1
                logger.error(f"Ошибка добавления SEO записи {page}.{lang}: {e}")
    
    def _sync_image_variable(self, page: str, key: str, supported_languages: List[str], results: Dict[str, int]):
        """Синхронизация переменной изображения"""
        try:
            # Проверяем, существует ли изображение данного типа
            existing = query_one(
                "SELECT id FROM images WHERE type = ?",
                (key,)
            )
            
            if not existing:
                # Создаем запись изображения с пустыми значениями
                execute(
                    "INSERT INTO images (name, path, original_path, type) VALUES (?, ?, ?, ?)",
                    ("", "", "", key)
                )
                results['added_variables'] += 1
                logger.debug(f"Добавлена переменная изображения: {page}.{key}")
                
                # Получаем ID созданного изображения
                image_id = query_one(
                    "SELECT id FROM images WHERE type = ? ORDER BY id DESC LIMIT 1",
                    (key,)
                )['id']
                
                # Создаем alt-тексты для всех языков
                for lang in supported_languages:
                    try:
                        execute(
                            "INSERT INTO images_alts (image_id, lang, alt_text) VALUES (?, ?, ?)",
                            (image_id, lang, "")
                        )
                        logger.debug(f"Добавлен alt-текст для изображения: {key}.{lang}")
                    except Exception as e:
                        logger.debug(f"Alt-текст уже существует: {key}.{lang}")
            else:
                results['skipped_variables'] += 1
                logger.debug(f"Изображение уже существует: {key}")
                
        except Exception as e:
            results['errors'] += 1
            logger.error(f"Ошибка добавления переменной изображения {page}.{key}: {e}")
    
    def _sync_image_alt_variable(self, page: str, key: str, supported_languages: List[str], results: Dict[str, int]):
        """Синхронизация alt-атрибута изображения"""
        try:
            # Извлекаем тип изображения из ключа (slider1_alt -> slider1)
            image_type = key.replace('_alt', '')
            
            # Проверяем, существует ли изображение данного типа
            image_record = query_one(
                "SELECT id FROM images WHERE type = ?",
                (image_type,)
            )
            
            if not image_record:
                # Сначала создаем запись изображения
                execute(
                    "INSERT INTO images (name, path, original_path, type) VALUES (?, ?, ?, ?)",
                    ("", "", "", image_type)
                )
                
                # Получаем ID созданного изображения
                image_record = query_one(
                    "SELECT id FROM images WHERE type = ? ORDER BY id DESC LIMIT 1",
                    (image_type,)
                )
                
                results['added_variables'] += 1
                logger.debug(f"Создана запись изображения для alt-атрибута: {image_type}")
            
            image_id = image_record['id']
            
            # Создаем alt-тексты для всех языков
            for lang in supported_languages:
                try:
                    # Проверяем, существует ли уже alt-текст
                    existing_alt = query_one(
                        "SELECT id FROM images_alts WHERE image_id = ? AND lang = ?",
                        (image_id, lang)
                    )
                    
                    if not existing_alt:
                        # Добавляем новый alt-текст
                        execute(
                            "INSERT INTO images_alts (image_id, lang, alt_text) VALUES (?, ?, ?)",
                            (image_id, lang, "")
                        )
                        results['added_variables'] += 1
                        logger.debug(f"Добавлен alt-текст для изображения: {image_type}.{lang}")
                    else:
                        results['skipped_variables'] += 1
                        logger.debug(f"Alt-текст уже существует: {image_type}.{lang}")
                        
                except Exception as e:
                    results['errors'] += 1
                    logger.error(f"Ошибка добавления alt-текста {image_type}.{lang}: {e}")
                    
        except Exception as e:
            results['errors'] += 1
            logger.error(f"Ошибка синхронизации alt-атрибута изображения {page}.{key}: {e}")
    
    def _sync_global_variables(self, variables: Set[str], supported_languages: List[str], results: Dict[str, int]):
        """Синхронизация глобальных переменных из base.html"""
        try:
            logger.info(f"Синхронизация глобальных переменных из base.html: {len(variables)} переменных")
            
            # Группируем переменные по namespace
            texts_vars = set()
            seo_vars = set()
            images_vars = set()
            images_alt_vars = set()
            
            for variable in variables:
                # Извлекаем namespace и ключ из переменной
                if '.' in variable:
                    namespace = variable.split('.')[0]
                    key = variable.split('.', 1)[1]
                else:
                    namespace = 'texts'  # fallback
                    key = variable
                
                # Группируем по namespace
                if namespace == 'texts':
                    texts_vars.add(key)
                elif namespace == 'seo':
                    seo_vars.add(key)
                elif namespace == 'images':
                    if key.endswith('_alt'):
                        images_alt_vars.add(key)
                    else:
                        images_vars.add(key)
                else:
                    logger.warning(f"Неподдерживаемый namespace в глобальных переменных: {namespace}")
            
            # Синхронизируем текстовые переменные как глобальные (page = 'global')
            for key in texts_vars:
                self._sync_text_variable('global', key, supported_languages, results)
            
            # Синхронизируем SEO переменные как глобальные
            if seo_vars:
                self._sync_seo_variables('global', seo_vars, supported_languages, results)
            
            # Синхронизируем переменные изображений
            for key in images_vars:
                self._sync_image_variable('global', key, supported_languages, results)
            
            # Синхронизируем alt-атрибуты изображений
            for key in images_alt_vars:
                self._sync_image_alt_variable('global', key, supported_languages, results)
            
            logger.info("Синхронизация глобальных переменных завершена")
            
        except Exception as e:
            logger.error(f"Ошибка синхронизации глобальных переменных: {e}")
            results['errors'] += 1
    
    def _sync_images_variables(self, page: str, template_keys: set, supported_languages: List[str], results: Dict[str, int]):
        """Синхронизация переменных изображений"""
        for key in template_keys:
            # Пропускаем alt-тексты, они обрабатываются в _sync_image_variable
            if key.endswith('_alt'):
                continue
                
            # Синхронизируем основную переменную изображения
            self._sync_image_variable(page, key, supported_languages, results)


    def full_sync_variables_to_database(self, supported_languages: List[str] = None) -> Dict[str, int]:
        """
        Полная синхронизация переменных с базой данных - удаляет неиспользуемые поля
        
        Args:
            supported_languages: Список поддерживаемых языков
            
        Returns:
            Словарь с результатами синхронизации
        """
        if supported_languages is None:
            supported_languages = get_supported_languages()
        
        results = {
            'parsed_pages': 0,
            'added_variables': 0,
            'removed_variables': 0,
            'skipped_variables': 0,
            'errors': 0
        }
        
        try:
            # Парсим все шаблоны
            template_variables = self.parse_all_templates()
            results['parsed_pages'] = len(template_variables)
            
            logger.info(f"Начинаем полную синхронизацию {len(template_variables)} страниц")
            
            for page, variables in template_variables.items():
                if page == 'unknown':
                    logger.warning("Пропускаем страницу 'unknown'")
                    continue
                
                logger.info(f"Полная синхронизация страницы {page} с {len(variables)} переменными")
                
                # Специальная обработка для base.html как глобального шаблона
                if page == 'base':
                    self._sync_global_variables(variables, supported_languages, results)
                    continue
                
                # Группируем переменные по namespace
                texts_vars = set()
                seo_vars = set()
                images_vars = set()
                images_alt_vars = set()  # Новый набор для alt-атрибутов
                
                for variable in variables:
                    if '.' in variable:
                        namespace = variable.split('.')[0]
                        key = variable.split('.', 1)[1]
                        
                        if namespace == 'texts':
                            texts_vars.add(key)
                        elif namespace == 'seo':
                            seo_vars.add(key)
                        elif namespace == 'images':
                            # Проверяем, является ли это alt-атрибутом
                            if key.endswith('_alt'):
                                images_alt_vars.add(key)
                            else:
                                images_vars.add(key)
                    else:
                        # Fallback для старых переменных
                        texts_vars.add(variable)
                
                # Синхронизируем текстовые переменные
                if texts_vars:
                    self._full_sync_text_variables(page, texts_vars, supported_languages, results)
                
                # Синхронизируем SEO переменные
                if seo_vars:
                    self._full_sync_seo_variables(page, seo_vars, supported_languages, results)
                
                # Синхронизируем переменные изображений
                if images_vars:
                    self._sync_images_variables(page, images_vars, supported_languages, results)
                
                # Синхронизируем alt-атрибуты изображений
                for key in images_alt_vars:
                    self._sync_image_alt_variable(page, key, supported_languages, results)
            
            logger.info(f"Полная синхронизация завершена: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка полной синхронизации переменных: {e}")
            results['errors'] += 1
            return results
    
    def _full_sync_text_variables(self, page: str, template_keys: set, supported_languages: List[str], results: Dict[str, int]):
        """Полная синхронизация текстовых переменных"""
        # Определяем таблицу в зависимости от типа страницы
        table_name = "texts_crm" if self._is_crm_page(page) else "texts"
        
        # Получаем текущие переменные в БД для этой страницы
        current_db_vars = set()
        db_results = query_all(
            f"SELECT DISTINCT key FROM {table_name} WHERE page = ?",
            (page,)
        )
        for row in db_results:
            current_db_vars.add(row['key'])
        
        # Добавляем новые переменные из шаблона
        new_vars = template_keys - current_db_vars
        for key in new_vars:
            for lang in supported_languages:
                try:
                    execute(
                        f"INSERT INTO {table_name} (page, key, lang, value) VALUES (?, ?, ?, ?)",
                        (page, key, lang, "")
                    )
                    results['added_variables'] += 1
                    logger.debug(f"Добавлена новая текстовая переменная: {page}.{key}.{lang}")
                except Exception as e:
                    results['errors'] += 1
                    logger.error(f"Ошибка добавления текстовой переменной {page}.{key}.{lang}: {e}")
        
        # Удаляем переменные, которых нет в шаблоне
        removed_vars = current_db_vars - template_keys
        for key in removed_vars:
            try:
                execute(
                    f"DELETE FROM {table_name} WHERE page = ? AND key = ?",
                    (page, key)
                )
                results['removed_variables'] += 1
                logger.info(f"Удалена неиспользуемая текстовая переменная: {page}.{key}")
            except Exception as e:
                results['errors'] += 1
                logger.error(f"Ошибка удаления текстовой переменной {page}.{key}: {e}")
        
        # Обновляем существующие переменные (если нужно)
        existing_vars = current_db_vars & template_keys
        for key in existing_vars:
            for lang in supported_languages:
                try:
                    # Проверяем, существует ли запись
                    existing = query_one(
                        "SELECT id FROM texts WHERE page = ? AND key = ? AND lang = ?",
                        (page, key, lang)
                    )
                    
                    if not existing:
                        # Добавляем отсутствующую языковую версию
                        execute(
                            "INSERT INTO texts (page, key, lang, value) VALUES (?, ?, ?, ?)",
                            (page, key, lang, "")
                        )
                        results['added_variables'] += 1
                        logger.debug(f"Добавлена языковая версия текста: {page}.{key}.{lang}")
                    else:
                        results['skipped_variables'] += 1
                        
                except Exception as e:
                    results['errors'] += 1
                    logger.error(f"Ошибка обновления текстовой переменной {page}.{key}.{lang}: {e}")
    
    def _full_sync_seo_variables(self, page: str, template_keys: set, supported_languages: List[str], results: Dict[str, int]):
        """Полная синхронизация SEO переменных"""
        # Для SEO переменных создаем записи для всех языков
        for lang in supported_languages:
            try:
                # Проверяем, существует ли SEO запись
                existing = query_one(
                    "SELECT id FROM seo WHERE page = ? AND lang = ?",
                    (page, lang)
                )
                
                if not existing:
                    # Добавляем новую SEO запись
                    execute(
                        "INSERT INTO seo (page, lang, title, description, keywords) VALUES (?, ?, ?, ?, ?)",
                        (page, lang, "", "", "")
                    )
                    results['added_variables'] += 1
                    logger.debug(f"Добавлена SEO запись: {page}.{lang}")
                else:
                    results['skipped_variables'] += 1
                    logger.debug(f"SEO запись уже существует: {page}.{lang}")
                    
            except Exception as e:
                results['errors'] += 1
                logger.error(f"Ошибка синхронизации SEO записи {page}.{lang}: {e}")
    
    def get_missing_variables(self, supported_languages: List[str] = None) -> Dict[str, List[str]]:
        """
        Возвращает переменные, которые есть в шаблонах, но отсутствуют в БД
        
        Args:
            supported_languages: Список поддерживаемых языков
            
        Returns:
            Словарь {страница: список_отсутствующих_переменных}
        """
        if supported_languages is None:
            supported_languages = get_supported_languages()
        
        missing = {}
        
        try:
            template_variables = self.parse_all_templates()
            
            for page, variables in template_variables.items():
                if page == 'unknown':
                    continue
                    
                missing_vars = []
                
                for variable in variables:
                    # Извлекаем ключ из переменной
                    if '.' in variable:
                        key = variable.split('.', 1)[1]
                    else:
                        key = variable
                    
                    # Проверяем наличие хотя бы одной языковой версии
                    has_any_lang = False
                    for lang in supported_languages:
                        existing = query_one(
                            "SELECT id FROM texts WHERE page = ? AND key = ? AND lang = ?",
                            (page, key, lang)
                        )
                        if existing:
                            has_any_lang = True
                            break
                    
                    if not has_any_lang:
                        missing_vars.append(variable)
                
                if missing_vars:
                    missing[page] = missing_vars
            
            return missing
            
        except Exception as e:
            logger.error(f"Ошибка получения отсутствующих переменных: {e}")
            return {}
    
    def get_database_variables(self, page: str = None) -> Dict[str, Dict[str, Dict[str, str]]]:
        """
        Получает все переменные из базы данных
        
        Args:
            page: Фильтр по странице (опционально)
            
        Returns:
            Словарь {страница: {ключ: {язык: значение}}}
        """
        try:
            db_variables = {}
            
            # Получаем текстовые переменные из обеих таблиц
            if page:
                # Определяем таблицу в зависимости от типа страницы
                table_name = "texts_crm" if self._is_crm_page(page) else "texts"
                query = f"SELECT page, key, lang, value FROM {table_name} WHERE page = ? ORDER BY page, key, lang"
                results = query_all(query, (page,))
            else:
                # Получаем из обеих таблиц
                query_public = "SELECT page, key, lang, value FROM texts ORDER BY page, key, lang"
                query_crm = "SELECT page, key, lang, value FROM texts_crm ORDER BY page, key, lang"
                results_public = query_all(query_public)
                results_crm = query_all(query_crm)
                results = results_public + results_crm
            
            for row in results:
                page_name = row['page']
                key = row['key']
                lang = row['lang']
                value = row['value']
                
                if page_name not in db_variables:
                    db_variables[page_name] = {}
                if key not in db_variables[page_name]:
                    db_variables[page_name][key] = {}
                
                db_variables[page_name][key][lang] = value
            
            # Получаем SEO переменные
            if page:
                seo_query = "SELECT page, lang, title, description, keywords FROM seo WHERE page = ? ORDER BY page, lang"
                seo_results = query_all(seo_query, (page,))
            else:
                seo_query = "SELECT page, lang, title, description, keywords FROM seo ORDER BY page, lang"
                seo_results = query_all(seo_query)
            
            for row in seo_results:
                page_name = row['page']
                lang = row['lang']
                
                if page_name not in db_variables:
                    db_variables[page_name] = {}
                
                # Добавляем SEO поля как отдельные ключи
                for field in ['title', 'description', 'keywords']:
                    key = f"seo_{field}"
                    if key not in db_variables[page_name]:
                        db_variables[page_name][key] = {}
                    db_variables[page_name][key][lang] = row[field] or ""
            
            # Получаем информацию об изображениях
            image_query = "SELECT type, COUNT(*) as count FROM images GROUP BY type"
            image_results = query_all(image_query)
            
            for row in image_results:
                image_type = row['type']
                count = row['count']
                
                # Добавляем информацию об изображениях как глобальные переменные
                if 'global' not in db_variables:
                    db_variables['global'] = {}
                
                key = f"images_{image_type}"
                if key not in db_variables['global']:
                    db_variables['global'][key] = {}
                
                # Для изображений не нужны языки, используем 'all'
                db_variables['global'][key]['all'] = str(count)
            
            return db_variables
            
        except Exception as e:
            logger.error(f"Ошибка получения переменных из БД: {e}")
            return {}
    
    def validate_template_syntax(self, template_path: str) -> Dict[str, List[str]]:
        """
        Проверяет синтаксис шаблона и возвращает найденные проблемы
        
        Args:
            template_path: Путь к файлу шаблона
            
        Returns:
            Словарь с найденными проблемами
        """
        issues = {
            'unclosed_tags': [],
            'invalid_syntax': [],
            'warnings': []
        }
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Проверяем незакрытые теги Jinja2
            open_tags = []
            for match in re.finditer(r'\{%\s*(\w+).*?%\}', content):
                tag = match.group(1)
                if tag in ['if', 'for', 'block']:
                    open_tags.append(tag)
                elif tag in ['endif', 'endfor', 'endblock']:
                    if not open_tags:
                        issues['invalid_syntax'].append(f"Неожиданный закрывающий тег {tag} на позиции {match.start()}")
                    else:
                        open_tags.pop()
            
            if open_tags:
                issues['unclosed_tags'] = open_tags
            
            # Проверяем корректность переменных
            for match in self.variable_pattern.findall(content):
                var = match.strip()
                if not self._is_parseable_variable(var):
                    if '.' in var and var.split('.')[0] not in self.supported_namespaces:
                        issues['warnings'].append(f"Неподдерживаемый namespace в переменной: {var}")
            
            return issues
            
        except Exception as e:
            logger.error(f"Ошибка валидации шаблона {template_path}: {e}")
            issues['invalid_syntax'].append(f"Ошибка чтения файла: {e}")
            return issues
