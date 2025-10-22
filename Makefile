# Makefile для CMS сайта-визитки
# Кроссплатформенные команды для разработки

.PHONY: help dev run tailwind-watch lint install clean test

# Цвета для вывода
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
RED=\033[0;31m
NC=\033[0m # No Color

# Определяем ОС
ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
    PYTHON := python
    PIP := pip
    NPM := npm
    ACTIVATE := venv\Scripts\activate
    SEP := \\
else
    DETECTED_OS := $(shell uname -s)
    PYTHON := python3
    PIP := pip3
    NPM := npm
    ACTIVATE := source venv/bin/activate
    SEP := /
endif

help: ## Показать справку
	@echo "$(GREEN)🚀 CMS для сайта-визитки$(NC)"
	@echo ""
	@echo "$(BLUE)Доступные команды:$(NC)"
	@echo "  $(YELLOW)dev$(NC)           - Запуск разработки (сервер + Tailwind watcher)"
	@echo "  $(YELLOW)run$(NC)            - Запуск только FastAPI сервера"
	@echo "  $(YELLOW)tailwind-watch$(NC) - Запуск Tailwind CSS watcher"
	@echo "  $(YELLOW)lint$(NC)           - Проверка кода"
	@echo "  $(YELLOW)install$(NC)        - Установка зависимостей"
	@echo "  $(YELLOW)clean$(NC)          - Очистка временных файлов"
	@echo "  $(YELLOW)test$(NC)           - Запуск тестов"
	@echo ""
	@echo "$(BLUE)ОС: $(DETECTED_OS)$(NC)"

dev: ## Запуск разработки (сервер + Tailwind watcher)
	@echo "$(GREEN)🚀 Запуск CMS для разработки...$(NC)"
ifeq ($(DETECTED_OS),Windows)
	@powershell -ExecutionPolicy Bypass -File dev.ps1
else
	@echo "$(YELLOW)На Windows используйте: .\dev.ps1$(NC)"
	@echo "$(YELLOW)Или запустите команды вручную:$(NC)"
	@echo "  $(BLUE)make install$(NC)"
	@echo "  $(BLUE)make tailwind-watch &$(NC)"
	@echo "  $(BLUE)make run$(NC)"
endif

run: ## Запуск только FastAPI сервера
	@echo "$(GREEN)🚀 Запуск FastAPI сервера...$(NC)"
ifeq ($(DETECTED_OS),Windows)
	@powershell -ExecutionPolicy Bypass -File run.ps1
else
	@echo "$(YELLOW)На Windows используйте: .\run.ps1$(NC)"
	@echo "$(YELLOW)Или запустите:$(NC)"
	@echo "  $(BLUE)uvicorn app.main:app --host 0.0.0.0 --port 8000$(NC)"
endif

tailwind-watch: ## Запуск Tailwind CSS watcher
	@echo "$(GREEN)🎨 Запуск Tailwind CSS watcher...$(NC)"
ifeq ($(DETECTED_OS),Windows)
	@powershell -ExecutionPolicy Bypass -File tailwind-watch.ps1
else
	@echo "$(YELLOW)На Windows используйте: .\tailwind-watch.ps1$(NC)"
	@echo "$(YELLOW)Или запустите:$(NC)"
	@echo "  $(BLUE)npm run tailwind:watch$(NC)"
endif

lint: ## Проверка кода
	@echo "$(GREEN)🔍 Запуск проверки кода...$(NC)"
ifeq ($(DETECTED_OS),Windows)
	@powershell -ExecutionPolicy Bypass -File lint.ps1
else
	@echo "$(YELLOW)На Windows используйте: .\lint.ps1$(NC)"
	@echo "$(YELLOW)Или установите инструменты и запустите:$(NC)"
	@echo "  $(BLUE)pip install flake8 black isort$(NC)"
	@echo "  $(BLUE)flake8 app/ --max-line-length=120$(NC)"
	@echo "  $(BLUE)black app/ --check --line-length=120$(NC)"
	@echo "  $(BLUE)isort app/ --check-only --profile black$(NC)"
endif

install: ## Установка зависимостей
	@echo "$(GREEN)📦 Установка зависимостей...$(NC)"
	@echo "$(BLUE)Проверяем Python...$(NC)"
	@$(PYTHON) --version
	@echo "$(BLUE)Создаем виртуальное окружение...$(NC)"
	@$(PYTHON) -m venv venv
ifeq ($(DETECTED_OS),Windows)
	@echo "$(BLUE)Активируем виртуальное окружение...$(NC)"
	@venv\Scripts\activate && pip install -r requirements.txt
	@echo "$(BLUE)Устанавливаем Node.js зависимости...$(NC)"
	@$(NPM) install
else
	@echo "$(BLUE)Активируем виртуальное окружение...$(NC)"
	@$(ACTIVATE) && $(PIP) install -r requirements.txt
	@echo "$(BLUE)Устанавливаем Node.js зависимости...$(NC)"
	@$(NPM) install
endif
	@echo "$(BLUE)Создаем необходимые директории...$(NC)"
	@mkdir -p data uploads/originals uploads/optimized cache/renders
	@echo "$(BLUE)Собираем CSS...$(NC)"
	@$(NPM) run build:css
	@echo "$(GREEN)✅ Зависимости установлены!$(NC)"

clean: ## Очистка временных файлов
	@echo "$(GREEN)🧹 Очистка временных файлов...$(NC)"
	@echo "$(BLUE)Удаляем __pycache__...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(BLUE)Удаляем .pyc файлы...$(NC)"
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(BLUE)Удаляем кэш...$(NC)"
	@rm -rf cache/renders/* 2>/dev/null || true
	@echo "$(BLUE)Удаляем node_modules...$(NC)"
	@rm -rf node_modules 2>/dev/null || true
	@echo "$(GREEN)✅ Очистка завершена!$(NC)"

test: ## Запуск тестов
	@echo "$(GREEN)🧪 Запуск тестов...$(NC)"
ifeq ($(DETECTED_OS),Windows)
	@powershell -ExecutionPolicy Bypass -File manage_tests.py
else
	@echo "$(YELLOW)На Windows используйте: python manage_tests.py$(NC)"
	@echo "$(YELLOW)Или запустите тесты вручную:$(NC)"
	@echo "  $(BLUE)python -m pytest tests/$(NC)"
endif

# Дополнительные команды
build: ## Сборка проекта
	@echo "$(GREEN)🔨 Сборка проекта...$(NC)"
	@$(NPM) run build:css
	@echo "$(GREEN)✅ Сборка завершена!$(NC)"

format: ## Форматирование кода
	@echo "$(GREEN)🎨 Форматирование кода...$(NC)"
	@$(ACTIVATE) && black app/ --line-length=120
	@$(ACTIVATE) && isort app/ --profile black
	@echo "$(GREEN)✅ Форматирование завершено!$(NC)"

check: lint ## Алиас для lint
	@echo "$(GREEN)✅ Проверка завершена!$(NC)"

# Информация о проекте
info: ## Информация о проекте
	@echo "$(GREEN)📋 Информация о проекте$(NC)"
	@echo "$(BLUE)ОС: $(DETECTED_OS)$(NC)"
	@echo "$(BLUE)Python: $(shell $(PYTHON) --version 2>/dev/null || echo 'Не найден')$(NC)"
	@echo "$(BLUE)Node.js: $(shell $(NPM) --version 2>/dev/null || echo 'Не найден')$(NC)"
	@echo "$(BLUE)Виртуальное окружение: $(shell if [ -d 'venv' ]; then echo 'Создано'; else echo 'Не создано'; fi)$(NC)"
	@echo "$(BLUE)Зависимости Python: $(shell if [ -f 'requirements.txt' ]; then echo 'requirements.txt найден'; else echo 'Не найден'; fi)$(NC)"
	@echo "$(BLUE)Зависимости Node.js: $(shell if [ -f 'package.json' ]; then echo 'package.json найден'; else echo 'Не найден'; fi)$(NC)"
