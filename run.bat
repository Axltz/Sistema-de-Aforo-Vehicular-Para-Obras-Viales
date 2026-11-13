@echo off
setlocal
cd /d "%~dp0"
title Roadwork Vehicle Traffic Monitor

echo ============================================================
echo   Roadwork Vehicle Traffic Monitoring System
echo ============================================================
echo.

REM ---------------------------------------------------------------
REM 1. Locate a Python interpreter (prefer 3.11, fall back to any)
REM ---------------------------------------------------------------
set "PY="
py -3.11 -c "import sys" >nul 2>nul && set "PY=py -3.11"
if not defined PY (
  python -c "import sys" >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo [ERROR] Python was not found on this computer.
  echo.
  echo Install Python 3.11 from https://www.python.org/downloads/
  echo IMPORTANT: check "Add Python to PATH" in the installer.
  echo.
  pause
  exit /b 1
)

REM ---------------------------------------------------------------
REM 2. Create the isolated environment (only the first time)
REM ---------------------------------------------------------------
if not exist ".venv\Scripts\python.exe" (
  echo [1/3] Creating the Python environment in .venv ...
  %PY% -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Could not create the virtual environment.
    pause
    exit /b 1
  )
)

set "VENV_PY=.venv\Scripts\python.exe"

REM ---------------------------------------------------------------
REM 3. Install dependencies (only the first time)
REM ---------------------------------------------------------------
if not exist ".venv\.deps-installed" (
  echo [2/3] Installing dependencies. The first run can take several minutes...
  "%VENV_PY%" -m pip install --upgrade pip >nul 2>nul
  "%VENV_PY%" -m pip install -r requirements-portable.txt
  if errorlevel 1 (
    echo.
    echo [ERROR] Dependency installation failed.
    echo Check your internet connection and try again.
    pause
    exit /b 1
  )
  echo ok> ".venv\.deps-installed"
)

echo [3/3] Starting...
echo.

REM ---------------------------------------------------------------
REM Modes:  run.bat         -> live CLI (opens windows)
REM         run.bat gui     -> desktop GUI
REM         run.bat demo    -> annotated demo video, no windows
REM         run.bat test    -> unit tests
REM ---------------------------------------------------------------
if /I "%~1"=="demo" goto demo
if /I "%~1"=="gui" goto gui
if /I "%~1"=="test" goto test

"%VENV_PY%" -m src.main %*
goto end

:demo
shift
"%VENV_PY%" -m scripts.demo %1 %2 %3 %4 %5 %6 %7 %8 %9
goto end

:gui
"%VENV_PY%" -m src.app
goto end

:test
"%VENV_PY%" -m pytest -q
goto end

:end
echo.
pause
