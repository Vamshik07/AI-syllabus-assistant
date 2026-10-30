@echo off
setlocal

set "ROOT=%~dp0"

if not exist "%ROOT%backend\venv\Scripts\python.exe" (
  echo Backend Python environment was not found:
  echo %ROOT%backend\venv\Scripts\python.exe
  pause
  exit /b 1
)

if not exist "%ROOT%frontend\package.json" (
  echo Frontend package.json was not found:
  echo %ROOT%frontend\package.json
  pause
  exit /b 1
)

start "AI Syllabus Assistant - Backend" /D "%ROOT%backend" cmd /k ".\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
start "AI Syllabus Assistant - Frontend" /D "%ROOT%frontend" cmd /k "npm run dev"

echo.
echo AI Syllabus Assistant is starting.
echo Backend:  http://localhost:8000/health
echo Frontend: http://localhost:3001
echo.
echo Keep both command windows open while using the application.
pause
