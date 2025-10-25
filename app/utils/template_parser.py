"""
Парсер HTML шаблонов для автоматического извлечения переменных
"""
import re
import os
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from app.database.db import execute, query_one, query_all

logger = logging.getLogger(__name__)


class TemplateParser:
    """Парсер HTML шаблонов для автоматического извлечения переменных"""
    
    def __init__(self, templates_dir: str = "app/templates"):
        self.templates_dir = Path(templates_dir)
        
        # Регулярные выражения для поиска переменных
        self.variable_pattern = re.compile(r'\{\{\s*([^}]+)\s*\}\}')
        self.conditional_pattern = re.compile(r'\{\%\s*if\s+([^%]+)\s*\%\}')
        
        # Системные переменные, которые исключаем из парсинга
        self.system_variables = {
            'lang', 'request', 'supported_languages', 'language_urls',
            'loop.index', 'loop.first', 'loop.last', 'loop.length',
            'temp', 'tmp', 'debug', 'config'
        }
        
        # Маппинг путей к страницам
        self.page_mapping = {
            'public/home.html': 'home',
            'public/about.html': 'about', 
            'public/catalog.html': 'catalog',
            'public/contacts.html': 'contacts'
        }
        
        # Поддерживаемые namespace для парсинга
        self.supported_namespaces = {'texts', 'seo'}
    
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
                var = match.strip()
                # Очищаем от фильтров и функций
                if '|' in var:
                    var = var.split('|')[0].strip()
                if ' or ' in var:
                    var = var.split(' or ')[0].strip()
                
                # Проверяем, что это переменная для парсинга
                if self._is_parseable_variable(var):
                    variables.add(var)
            
            # Ищем переменные в условиях
            for match in self.conditional_pattern.findall(content):
                var = match.strip()
                # Очищаем от операторов сравнения
                if ' == ' in var:
                    var = var.split(' == ')[0].strip()
                elif ' != ' in var:
                    var = var.split(' != ')[0].strip()
                elif ' in ' in var:
                    var = var.split(' in ')[0].strip()
                
                if self._is_parseable_variable(var):
                    variables.add(var)
            
            logger.debug(f"Найдено {len(variables)} переменных в {template_path}: {variables}")
            return variables
            
        except Exception as e:
            logger.error(f"Ошибка парсинга шаблона {template_path}: {e}")
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
        Определяет страницу по пути к шаблону
        
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
                
                # Возвращаем страницу из маппинга
                page = self.page_mapping.get(template_name, 'unknown')
                logger.debug(f"Определена страница {page} для {template_path} (template_name: {template_name}, mapping: {self.page_mapping})")
                return page
                
            except ValueError:
                # Если не можем найти относительный путь, пробуем по имени файла
                template_name = 'public/' + path.name
                page = self.page_mapping.get(template_name, 'unknown')
                logger.debug(f"Определена страница {page} для {template_path} (по имени файла)")
                return page
                
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
        Синхронизирует найденные переменные с базой данных
        
        Args:
            supported_languages: Список поддерживаемых языков
            
        Returns:
            Словарь с результатами синхронизации
        """
        if supported_languages is None:
            supported_languages = ['en', 'ru', 'ua']
        
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
                
                for variable in variables:
                    # Извлекаем ключ из переменной (texts.title -> title)
                    if '.' in variable:
                        key = variable.split('.', 1)[1]
                    else:
                        key = variable
                    
                    for lang in supported_languages:
                        try:
                            # Проверяем, существует ли уже запись
                            existing = query_one(
                                "SELECT id FROM texts WHERE page = ? AND key = ? AND lang = ?",
                                (page, key, lang)
                            )
                            
                            if not existing:
                                # Добавляем новую переменную с пустым значением
                                execute(
                                    "INSERT INTO texts (page, key, lang, value) VALUES (?, ?, ?, ?)",
                                    (page, key, lang, "")
                                )
                                results['added_variables'] += 1
                                logger.debug(f"Добавлена переменная: {page}.{key}.{lang}")
                            else:
                                results['skipped_variables'] += 1
                                logger.debug(f"Переменная уже существует: {page}.{key}.{lang}")
                                
                        except Exception as e:
                            results['errors'] += 1
                            logger.error(f"Ошибка добавления переменной {page}.{key}.{lang}: {e}")
            
            logger.info(f"Синхронизация завершена: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка синхронизации переменных: {e}")
            results['errors'] += 1
            return results
    
    def get_missing_variables(self, supported_languages: List[str] = None) -> Dict[str, List[str]]:
        """
        Возвращает переменные, которые есть в шаблонах, но отсутствуют в БД
        
        Args:
            supported_languages: Список поддерживаемых языков
            
        Returns:
            Словарь {страница: список_отсутствующих_переменных}
        """
        if supported_languages is None:
            supported_languages = ['en', 'ru', 'ua']
        
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
            if page:
                # Получаем переменные для конкретной страницы
                query = "SELECT page, key, lang, value FROM texts WHERE page = ? ORDER BY page, key, lang"
                results = query_all(query, (page,))
            else:
                # Получаем все переменные
                query = "SELECT page, key, lang, value FROM texts ORDER BY page, key, lang"
                results = query_all(query)
            
            db_variables = {}
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
