@echo off
title ProctorAI — Development Server
color 0A

echo.
echo  ========================================================
echo           ProctorAI — Development Server
echo           Building and Starting All Services
echo  ========================================================
echo.

:: ── Docker check ─────────────────────────────────────────────
echo [1/4] Checking Docker Desktop...
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo  ERROR: Docker Desktop is not running!
    echo  Start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)
echo  OK — Docker Desktop is running
echo.

:: ── Stop old containers ──────────────────────────────────────
echo [2/4] Stopping old containers (if any)...
docker-compose down --remove-orphans 2>nul
echo  OK — Old containers stopped
echo.

:: ── Build and start ──────────────────────────────────────────
echo [3/4] Building and starting all services (3-5 min)...
echo.
echo  Services:
echo    PostgreSQL 17  (port 5432) — DB: proctoring_db
echo    Redis 7        (port 6379) — cache
echo    Kafka 3.7      (port 9092) — event queue
echo    Backend Java   (port 9090) — Spring Boot API
echo    AI Service     (port 8000) — Python/FastAPI + YOLOv8 + MediaPipe
echo    Analytics      (port 8082) — analytics
echo    Frontend       (port 80)   — Nginx + HTML/JS
echo.

docker-compose up -d --build

if %ERRORLEVEL% neq 0 (
    echo.
    echo  ERROR: Build failed! Check logs:
    echo  docker-compose logs --tail=50
    echo.
    pause
    exit /b 1
)

echo.
echo  OK — All containers started!
echo.

:: ── Wait for services ────────────────────────────────────────
echo [4/4] Waiting for services to be ready...
echo.

:: Wait for PostgreSQL
echo  ... PostgreSQL
:wait_pg
docker exec proktorai-postgres pg_isready -U postgres >nul 2>&1
if %ERRORLEVEL% neq 0 (
    timeout /t 2 /nobreak >nul
    goto wait_pg
)
echo  OK — PostgreSQL ready (DB: proctoring_db, user: postgres, pass: 1234)

:: Wait for Backend (max 120 sec)
echo  ... Backend (Spring Boot)
set /a count=0
:wait_backend
curl -sf http://localhost:9090/actuator/health >nul 2>&1
if %ERRORLEVEL% neq 0 (
    set /a count+=3
    if %count% geq 120 (
        echo  WARN — Backend still loading... check: docker logs proktorai-backend
        goto skip_backend
    )
    timeout /t 3 /nobreak >nul
    goto wait_backend
)
echo  OK — Backend ready (port 9090)
:skip_backend

:: Wait for AI Service
echo  ... AI Service (FastAPI + YOLOv8)
set /a count=0
:wait_ai
curl -sf http://localhost:8000/health >nul 2>&1
if %ERRORLEVEL% neq 0 (
    set /a count+=3
    if %count% geq 90 (
        echo  WARN — AI Service still loading... check: docker logs proktorai-ai
        goto skip_ai
    )
    timeout /t 3 /nobreak >nul
    goto wait_ai
)
echo  OK — AI Service ready (port 8000)
:skip_ai

:: ── Result ───────────────────────────────────────────────────
echo.
echo  ========================================================
echo              ProctorAI STARTED SUCCESSFULLY!
echo  ========================================================
echo.
echo   Frontend:      http://localhost
echo   Backend API:   http://localhost:9090/api/v1
echo   AI Service:    http://localhost:8000
echo   Analytics:     http://localhost:8082
echo.
echo   PostgreSQL:    localhost:5432
echo     DB:          proctoring_db
echo     User:        postgres
echo     Password:    1234
echo.
echo   Demo accounts:
echo     student@demo.kz / demo123  (Student)
echo     teacher@demo.kz / demo123  (Teacher)
echo     admin@demo.kz   / demo123  (Admin)
echo.
echo   Commands:
echo     docker-compose logs -f       — live logs
echo     docker-compose down          — stop all
echo     docker-compose restart ai    — restart AI
echo  ========================================================
echo.

:: Open browser
echo  Opening http://localhost in browser...
start http://localhost

echo.
echo  Press any key to exit (containers will keep running)
pause >nul
