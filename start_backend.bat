@echo off
chcp 65001 >nul
title NortGru — Backend (FastAPI)
echo ============================================
echo   NortGru — Запуск Backend
echo ============================================
echo.

cd /d "%~dp0backend"

:: Определяем команду Python (py -> python3 -> python)
set PYTHON_CMD=
where py >nul 2>&1 && set PYTHON_CMD=py
if "%PYTHON_CMD%"=="" where python3 >nul 2>&1 && set PYTHON_CMD=python3
if "%PYTHON_CMD%"=="" where python  >nul 2>&1 && set PYTHON_CMD=python
if "%PYTHON_CMD%"=="" (
    echo ОШИБКА: Python не найден. Установите: https://www.python.org/downloads/
    pause & exit /b 1
)
echo Используется: %PYTHON_CMD%
%PYTHON_CMD% --version

:: Создаём venv если нет
if not exist "venv\Scripts\activate.bat" (
    echo.
    echo [1/3] Создание виртуального окружения...
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 ( echo ОШИБКА: не удалось создать venv. & pause & exit /b 1 )
)

:: Активируем venv
echo [2/3] Активация виртуального окружения...
call venv\Scripts\activate.bat

:: Устанавливаем зависимости
echo [3/3] Установка зависимостей...
pip install --upgrade pip -q
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ОШИБКА: не удалось установить зависимости!
    echo Попробуйте удалить папку backend\venv и запустить снова.
    pause & exit /b 1
)

echo.
echo ============================================
echo   Backend запущен:  http://localhost:8000
echo   Swagger API docs: http://localhost:8000/api/docs
echo   Для остановки нажмите Ctrl+C
echo ============================================
echo.

uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
