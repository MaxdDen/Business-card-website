# Скрипт для запуска разработки
# Запускает FastAPI сервер и Tailwind CSS watcher одновременно

Write-Host "🚀 Запуск CMS для разработки..." -ForegroundColor Green

# Проверяем наличие Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python найден: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python не найден! Установите Python 3.12+" -ForegroundColor Red
    exit 1
}

# Проверяем наличие Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✅ Node.js найден: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js не найден! Установите Node.js для работы с Tailwind CSS" -ForegroundColor Red
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

# Устанавливаем зависимости Python если нужно
if (-not (Test-Path "venv")) {
    Write-Host "📦 Создаем виртуальное окружение..." -ForegroundColor Blue
    python -m venv venv
}

Write-Host "📦 Активируем виртуальное окружение..." -ForegroundColor Blue
& "venv\Scripts\Activate.ps1"

Write-Host "📦 Устанавливаем Python зависимости..." -ForegroundColor Blue
pip install -r requirements.txt

# Устанавливаем Node.js зависимости если нужно
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Устанавливаем Node.js зависимости..." -ForegroundColor Blue
    npm install
}

# Создаем необходимые директории
$directories = @("data", "uploads", "uploads\originals", "uploads\optimized", "cache", "cache\renders")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "📁 Создана директория: $dir" -ForegroundColor Blue
    }
}

Write-Host "🎨 Собираем CSS..." -ForegroundColor Blue
npm run build:css

Write-Host "🚀 Запускаем серверы..." -ForegroundColor Green
Write-Host "📡 FastAPI сервер: http://localhost:8000" -ForegroundColor Cyan
Write-Host "🎨 Tailwind CSS watcher активен" -ForegroundColor Cyan
Write-Host "📝 CMS: http://localhost:8000/cms" -ForegroundColor Cyan
Write-Host "🌐 Публичный сайт: http://localhost:8000/" -ForegroundColor Cyan
Write-Host ""
Write-Host "Для остановки нажмите Ctrl+C" -ForegroundColor Yellow
Write-Host ""

# Запускаем FastAPI сервер в фоне
$fastapiJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    & "venv\Scripts\Activate.ps1"
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# Запускаем Tailwind watcher в фоне
$tailwindJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    npm run tailwind:watch
}

# Ждем завершения любого из процессов
try {
    Wait-Job -Job $fastapiJob, $tailwindJob -Any
} finally {
    # Останавливаем все задачи
    Stop-Job -Job $fastapiJob, $tailwindJob -ErrorAction SilentlyContinue
    Remove-Job -Job $fastapiJob, $tailwindJob -ErrorAction SilentlyContinue
    Write-Host "🛑 Серверы остановлены" -ForegroundColor Yellow
}
