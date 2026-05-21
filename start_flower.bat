@echo off
REM Start Flower dashboard for Celery monitoring

cd /d "%~dp0"

REM Activate venv
call venv\Scripts\activate.bat

REM Run Flower
celery -A app.celery_app flower --port=5555
