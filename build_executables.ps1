# Build script for AI File Organizer executables
# This script builds both the standard and multi-threaded versions

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI File Organizer - Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check and install required dependencies
Write-Host "Installing/Updating all required dependencies..." -ForegroundColor Yellow
Write-Host "This may take a few minutes on first run..." -ForegroundColor Cyan

# Install all dependencies from requirements.txt
if (Test-Path "requirements.txt") {
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install dependencies. Exiting." -ForegroundColor Red
        exit 1
    }
    Write-Host "All dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host "requirements.txt not found. Installing core dependencies..." -ForegroundColor Yellow
    python -m pip install PyQt5 requests langchain langchain-ollama cryptography pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install dependencies. Exiting." -ForegroundColor Red
        exit 1
    }
    Write-Host "Core dependencies installed successfully!" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Building FIelOrganizer.exe (Standard Version)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
python -m PyInstaller FIelOrganizer.spec --clean

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ FIelOrganizer.exe built successfully!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "✗ Failed to build FIelOrganizer.exe" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Building FilelOrganizer_MT.exe (Multi-threaded Version)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
python -m PyInstaller FilelOrganizer_MT.spec --clean

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ FilelOrganizer_MT.exe built successfully!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "✗ Failed to build FilelOrganizer_MT.exe" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Build Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Executables are located in the 'dist' folder:" -ForegroundColor Yellow
Write-Host "  - dist\FIelOrganizer.exe (Standard version)" -ForegroundColor White
Write-Host "  - dist\FilelOrganizer_MT.exe (Multi-threaded version)" -ForegroundColor White
Write-Host ""
Write-Host "Both versions now include LM Studio support!" -ForegroundColor Cyan
Write-Host ""

