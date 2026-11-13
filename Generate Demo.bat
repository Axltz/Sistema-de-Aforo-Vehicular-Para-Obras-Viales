@echo off
REM ============================================================================
REM  DOUBLE-CLICK THIS FILE to generate an annotated demo video (no windows).
REM  Output: demo\demo_trafico1.mp4 + demo\demo_summary.json
REM ============================================================================
cd /d "%~dp0"
title Roadwork Vehicle Traffic Monitor - Demo Generator
call "%~dp0run.bat" demo
