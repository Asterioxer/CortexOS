@echo off
title CortexOS // Neural Quantum Core HUD
cd /d "%~dp0"
echo ========================================================
echo   Launching CortexOS Native Holographic Desktop HUD...
echo ========================================================

:: Check if Ollama is running; launch silently in background if offline
curl.exe -s http://127.0.0.1:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [*] Starting local Ollama server in background...
    wscript.exe "%~dp0scripts\run_ollama_silent.vbs" >nul 2>&1
    timeout /t 3 /nobreak >nul
)

"%~dp0.venv\Scripts\python.exe" cortex/companion_hud.py

if errorlevel 1 (
    echo.
    echo CortexOS Companion HUD encountered an error.
    pause
)
