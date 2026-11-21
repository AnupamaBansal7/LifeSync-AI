@echo off
title LifeSync AI 3.0 Companion
echo Starting LifeSync AI 3.0 Desktop Companion Pet ("Sync")...
if exist "backend\.venv\Scripts\python.exe" (
    backend\.venv\Scripts\python.exe desktop\pet_companion.py
) else if exist "..\backend\.venv\Scripts\python.exe" (
    ..\backend\.venv\Scripts\python.exe desktop\pet_companion.py
) else (
    python desktop\pet_companion.py
)
pause
