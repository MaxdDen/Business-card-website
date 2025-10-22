# Скрипт для запуска Tailwind CSS watcher
# Следит за изменениями в CSS и автоматически пересобирает

Write-Host "🎨 Запуск Tailwind CSS watcher..." -ForegroundColor Green

# Проверяем наличие Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✅ Node.js найден: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js не найден! Установите Node.js для работы с Tailwind CSS" -ForegroundColor Red
    exit 1
}

# Проверяем наличие package.json
if (-not (Test-Path "package.json")) {
    Write-Host "❌ package.json не найден! Инициализируйте проект с Tailwind CSS" -ForegroundColor Red
    exit 1
}

# Устанавливаем зависимости если нужно
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Устанавливаем Node.js зависимости..." -ForegroundColor Blue
    npm install
}

# Проверяем наличие input.css
if (-not (Test-Path "app\static\css\input.css")) {
    Write-Host "❌ app\static\css\input.css не найден!" -ForegroundColor Red
    Write-Host "Создайте файл с содержимым: @import 'tailwindcss';" -ForegroundColor Yellow
    exit 1
}

Write-Host "🎨 Запускаем Tailwind CSS watcher..." -ForegroundColor Green
Write-Host "📁 Отслеживаем: app\static\css\input.css" -ForegroundColor Cyan
Write-Host "📁 Вывод: app\static\css\output.css" -ForegroundColor Cyan
Write-Host ""
Write-Host "Для остановки нажмите Ctrl+C" -ForegroundColor Yellow
Write-Host ""

# Запускаем watcher
npm run tailwind:watch
