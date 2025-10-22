# Скрипт для запуска только FastAPI сервера
# Используется для production или когда Tailwind уже собран

Write-Host "🚀 Запуск FastAPI сервера..." -ForegroundColor Green

# Проверяем наличие Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python найден: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python не найден! Установите Python 3.12+" -ForegroundColor Red
    exit 1
}

# Проверяем наличие .env файла
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Файл .env не найден. Создайте его на основе .env.example" -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Write-Host "📋 Копируем .env.example в .env..." -ForegroundColor Blue
        Copy-Item ".env.example" ".env"
        Write-Host "✅ Файл .env создан. Отредактируйте его при необходимости." -ForegroundColor Green
    }
}

# Активируем виртуальное окружение если есть
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "📦 Активируем виртуальное окружение..." -ForegroundColor Blue
    & "venv\Scripts\Activate.ps1"
}

# Проверяем наличие CSS файла
if (-not (Test-Path "app\static\css\output.css")) {
    Write-Host "⚠️  CSS файл не найден. Собираем..." -ForegroundColor Yellow
    if (Test-Path "package.json") {
        npm run build:css
    } else {
        Write-Host "❌ package.json не найден. Установите Tailwind CSS вручную" -ForegroundColor Red
        exit 1
    }
}

# Создаем необходимые директории
$directories = @("data", "uploads", "uploads\originals", "uploads\optimized", "cache", "cache\renders")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "📁 Создана директория: $dir" -ForegroundColor Blue
    }
}

Write-Host "🚀 Запускаем FastAPI сервер..." -ForegroundColor Green
Write-Host "📡 Сервер: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📝 CMS: http://localhost:8000/cms" -ForegroundColor Cyan
Write-Host "🌐 Публичный сайт: http://localhost:8000/" -ForegroundColor Cyan
Write-Host "📚 API документация: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Для остановки нажмите Ctrl+C" -ForegroundColor Yellow
Write-Host ""

# Запускаем сервер
uvicorn app.main:app --host 0.0.0.0 --port 8000
