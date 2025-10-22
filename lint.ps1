# Скрипт для проверки кода (linting)
# Проверяет Python код на соответствие стандартам

Write-Host "🔍 Запуск проверки кода..." -ForegroundColor Green

# Проверяем наличие Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python найден: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python не найден! Установите Python 3.12+" -ForegroundColor Red
    exit 1
}

# Активируем виртуальное окружение если есть
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "📦 Активируем виртуальное окружение..." -ForegroundColor Blue
    & "venv\Scripts\Activate.ps1"
}

# Устанавливаем инструменты линтинга если нужно
Write-Host "📦 Проверяем инструменты линтинга..." -ForegroundColor Blue

$lintingTools = @("flake8", "black", "isort")
$missingTools = @()

foreach ($tool in $lintingTools) {
    try {
        $version = & $tool --version 2>&1
        Write-Host "✅ $tool найден" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  $tool не найден, устанавливаем..." -ForegroundColor Yellow
        $missingTools += $tool
    }
}

if ($missingTools.Count -gt 0) {
    Write-Host "📦 Устанавливаем инструменты линтинга..." -ForegroundColor Blue
    pip install flake8 black isort
}

Write-Host ""
Write-Host "🔍 Проверяем Python код с помощью flake8..." -ForegroundColor Blue
flake8 app/ --max-line-length=120 --ignore=E203,W503

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ flake8: Код соответствует стандартам" -ForegroundColor Green
} else {
    Write-Host "⚠️  flake8: Найдены проблемы в коде" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎨 Проверяем форматирование с помощью black..." -ForegroundColor Blue
black app/ --check --line-length=120

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ black: Код правильно отформатирован" -ForegroundColor Green
} else {
    Write-Host "⚠️  black: Код требует форматирования" -ForegroundColor Yellow
    Write-Host "💡 Запустите: black app/ --line-length=120" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "📦 Проверяем импорты с помощью isort..." -ForegroundColor Blue
isort app/ --check-only --profile black

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ isort: Импорты правильно отсортированы" -ForegroundColor Green
} else {
    Write-Host "⚠️  isort: Импорты требуют сортировки" -ForegroundColor Yellow
    Write-Host "💡 Запустите: isort app/ --profile black" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "🔍 Проверяем CSS с помощью stylelint..." -ForegroundColor Blue

# Проверяем наличие stylelint
try {
    $stylelintVersion = npx stylelint --version 2>&1
    Write-Host "✅ stylelint найден" -ForegroundColor Green
    
    # Проверяем CSS файл
    if (Test-Path "app\static\css\output.css") {
        npx stylelint "app\static\css\output.css" --config .stylelintrc.json
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ stylelint: CSS соответствует стандартам" -ForegroundColor Green
        } else {
            Write-Host "⚠️  stylelint: Найдены проблемы в CSS" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️  CSS файл не найден, пропускаем проверку" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  stylelint не найден, пропускаем проверку CSS" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎯 Проверка завершена!" -ForegroundColor Green
Write-Host "💡 Для автоматического исправления запустите:" -ForegroundColor Cyan
Write-Host "   black app/ --line-length=120" -ForegroundColor White
Write-Host "   isort app/ --profile black" -ForegroundColor White
