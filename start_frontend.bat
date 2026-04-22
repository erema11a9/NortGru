@echo off
chcp 65001 >nul
title NortGru — Frontend (Vue 3 + Vite)
echo ============================================
echo   NortGru — Запуск Frontend
echo ============================================
echo.

cd /d "%~dp0frontend"

:: Проверяем node_modules
if not exist "node_modules" (
    echo [1/2] Установка npm-зависимостей...
    call npm install
    if errorlevel 1 (
        echo ОШИБКА: не удалось установить зависимости.
        echo Убедитесь что Node.js установлен: https://nodejs.org
        pause
        exit /b 1
    )
)

echo [2/2] Запуск Vite dev-server...
echo.
echo ============================================
echo   Frontend запускается на http://localhost:5173
echo   Backend должен быть запущен на :8000
echo   Для остановки нажмите Ctrl+C
echo ============================================
echo.

call npm run dev

pause
