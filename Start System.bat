@echo off
REM ============================================================================
REM  DOUBLE-CLICK THIS FILE to open the desktop application.
REM  It reuses (or creates) the Python environment automatically.
REM ============================================================================
cd /d "%~dp0"
title Roadwork Vehicle Traffic Monitor - Desktop App
call "%~dp0run.bat" gui
