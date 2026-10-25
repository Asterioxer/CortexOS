@echo off
title J.A.R.V.I.S. // STARK-OS AI Companion
cd /d "%~dp0"
echo ========================================================
echo Starting J.A.R.V.I.S. Arc Reactor Desktop Companion...
echo ========================================================

:: Check if Ollama is running; launch silently in background if offline
curl.exe -s http://127.0.0.1:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [*] Starting local Ollama server in background...
    wscript.exe "%~dp0run_ollama_silent.vbs" >nul 2>&1
    timeout /t 3 /nobreak >nul
)

if "%1"=="--cli" (
    echo [*] Launching in Terminal CLI mode...
    "%~dp0oi_env\Scripts\python.exe" voice_assistant.py
) else (
    echo [*] Launching Native J.A.R.V.I.S. Arc Reactor Desktop HUD...
    "%~dp0oi_env\Scripts\python.exe" desktop_companion.py
)

if errorlevel 1 (
    echo.
    echo Assistant encountered an error.
    pause
)
