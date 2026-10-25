@echo off
title CortexOS // Neural Voice & Somatosensory Assistant
cd /d "%~dp0"
echo ========================================================
echo   CortexOS Autonomous Neural Voice & Somatosensory Host
echo ========================================================

:: Check if Ollama is running; launch silently in background if offline
curl.exe -s http://127.0.0.1:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [*] Starting local Ollama server in background...
    wscript.exe "%~dp0scripts\run_ollama_silent.vbs" >nul 2>&1
    timeout /t 3 /nobreak >nul
)

echo [*] Launching CortexOS Full-Duplex Voice Assistant...
"%~dp0.venv\Scripts\python.exe" -m cortex.voice_assistant

if errorlevel 1 (
    echo.
    echo CortexOS Voice Assistant exited with an error.
    pause
)
