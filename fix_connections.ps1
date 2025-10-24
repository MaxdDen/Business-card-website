# Script for fixing hanging connections
Write-Host "Fixing hanging server connections" -ForegroundColor Yellow
Write-Host "=" * 50

# 1. Kill all Python processes
Write-Host "Killing Python processes..." -ForegroundColor Cyan
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process uvicorn -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# 2. Clear TCP connections (requires admin rights)
Write-Host "Clearing TCP connections..." -ForegroundColor Cyan
try {
    netsh int ip reset | Out-Null
    netsh winsock reset | Out-Null
    Write-Host "TCP connections cleared" -ForegroundColor Green
} catch {
    Write-Host "Admin rights required for TCP cleanup" -ForegroundColor Yellow
}

# 3. Check port 8000
Write-Host "Checking port 8000..." -ForegroundColor Cyan
$port8000 = netstat -an | Select-String ":8000"
if ($port8000) {
    Write-Host "Port 8000 still occupied:" -ForegroundColor Yellow
    $port8000 | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host "Port 8000 is free" -ForegroundColor Green
}

# 4. Create .env file if missing
Write-Host "Checking .env file..." -ForegroundColor Cyan
if (-not (Test-Path ".env")) {
    if (Test-Path "env.example") {
        Copy-Item "env.example" ".env"
        Write-Host ".env file created from env.example" -ForegroundColor Green
    } else {
        Write-Host "env.example file not found" -ForegroundColor Red
    }
} else {
    Write-Host ".env file exists" -ForegroundColor Green
}

# 5. Server startup
Write-Host "Starting server..." -ForegroundColor Cyan
Write-Host "Use: python start_server.py" -ForegroundColor Yellow
Write-Host "Or: uvicorn app.main:app --reload --host 127.0.0.1 --port 8000" -ForegroundColor Yellow

Write-Host "`nDone! You can now start the server." -ForegroundColor Green
