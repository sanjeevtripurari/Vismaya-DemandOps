@echo off
REM Cross-platform Docker startup script for Vismaya DemandOps (Windows)
REM Works on Windows Command Prompt and PowerShell

setlocal enabledelayedexpansion

echo 🚀 Starting Vismaya DemandOps
echo ==================================

REM Configuration
set PROJECT_NAME=Vismaya DemandOps
set CONTAINER_NAME=vismaya-demandops
set HEALTH_URL=http://localhost:8501/_stcore/health
set APP_URL=http://localhost:8501

REM Check prerequisites
echo ℹ️ Checking prerequisites...

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not found. Please install Docker Desktop.
    echo Download from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    docker compose version >nul 2>&1
    if errorlevel 1 (
        echo ❌ Docker Compose not found. Please install Docker Compose.
        pause
        exit /b 1
    ) else (
        set COMPOSE_CMD=docker compose
    )
) else (
    set COMPOSE_CMD=docker-compose
)

echo ✅ Docker and Docker Compose found

REM Setup environment
echo ℹ️ Setting up environment...

REM Check if .env exists
if not exist "../.env" (
    if exist "../.env.example" (
        echo ℹ️ Creating .env from template...
        copy "..\\.env.example" "..\\.env" >nul
        echo ⚠️ Please edit .env with your AWS credentials
        echo Required variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
        pause
    ) else (
        echo ❌ .env.example not found
        pause
        exit /b 1
    )
)

REM Create logs directory
if not exist "../logs" mkdir "../logs"

echo ✅ Environment setup complete

REM Start services
echo ℹ️ Starting Docker services...

REM Stop any existing containers
%COMPOSE_CMD% down >nul 2>&1

REM Build and start
%COMPOSE_CMD% up -d --build
if errorlevel 1 (
    echo ❌ Failed to start services
    pause
    exit /b 1
)

echo ✅ Services started successfully

REM Wait for health check
echo ℹ️ Waiting for application to be ready...

set /a attempt=1
set /a max_attempts=30

:health_check_loop
curl -f %HEALTH_URL% >nul 2>&1
if not errorlevel 1 (
    echo ✅ Application is healthy and ready!
    goto :health_check_done
)

echo|set /p="."
timeout /t 2 /nobreak >nul
set /a attempt+=1
if !attempt! leq !max_attempts! goto :health_check_loop

echo ⚠️ Application failed to become healthy
echo ℹ️ Check logs with: %COMPOSE_CMD% logs -f

:health_check_done

REM Show status
echo.
echo 🎉 %PROJECT_NAME% is running!
echo.
echo 📊 Application URL: %APP_URL%
echo 📋 View logs: %COMPOSE_CMD% logs -f
echo 🛑 Stop services: %COMPOSE_CMD% down
echo.

REM Try to open browser
start %APP_URL% >nul 2>&1

echo Press any key to exit...
pause >nul