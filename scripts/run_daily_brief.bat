@echo off
cd /d "c:\Users\oussa\Downloads\aios-starter-kit\aios-starter-kit"
set PYTHONIOENCODING=utf-8
.venv\Scripts\python scripts\collect.py >> data\collect.log 2>&1
.venv\Scripts\python scripts\daily_brief.py --preset solo >> data\daily-brief.log 2>&1
