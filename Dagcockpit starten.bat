@echo off
rem Start de dagcockpit en opent hem in de browser (http://127.0.0.1:5070).
cd /d "%~dp0"
start "" http://127.0.0.1:5070
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" apps\dagcockpit\cockpit.py
) else (
    python apps\dagcockpit\cockpit.py
)
