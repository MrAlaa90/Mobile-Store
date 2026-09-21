@echo off
chcp 65001 > nul
echo ========================================================
echo   MOBILE STORE - DOCKER COMPOSE LAUNCHER
echo   PostgreSQL + Django API + React Dashboard
echo ========================================================
echo.

echo [1/3] Checking Docker Compose configuration...
docker compose config --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Docker daemon is not running or Docker Desktop is not started.
    echo Please make sure Docker Desktop is open and running, then try again.
    pause
    exit /b 1
)

echo [2/3] Building and starting all containers...
docker compose up -d --build

echo.
echo [3/3] Waiting for services to initialize...
timeout /t 10 /nobreak > nul

echo.
echo Running integration test...
python scripts/verify_docker_stack.py

echo.
echo ========================================================
echo   Stack is running!
echo   - Web Dashboard:   http://localhost:3000
echo   - Backend REST API: http://localhost:8000/api
echo   - Admin Login:     admin / admin123
echo ========================================================
pause
