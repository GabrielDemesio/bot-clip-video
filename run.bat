@echo off
REM Video Lesson Splitter - Helper Script for Windows
REM Usage: run.bat [command]

setlocal enabledelayedexpansion

REM Check if Docker is installed
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker not found. Please install Docker Desktop first.
    echo Visit: https://docs.docker.com/desktop/install/windows-install/
    exit /b 1
)

where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose not found. Please install Docker Compose first.
    exit /b 1
)

REM Get command
set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=help

REM Execute command
if "%COMMAND%"=="build" goto build
if "%COMMAND%"=="run" goto run
if "%COMMAND%"=="detached" goto detached
if "%COMMAND%"=="bg" goto detached
if "%COMMAND%"=="logs" goto logs
if "%COMMAND%"=="stop" goto stop
if "%COMMAND%"=="clean" goto clean
if "%COMMAND%"=="shell" goto shell
if "%COMMAND%"=="bash" goto shell
if "%COMMAND%"=="stats" goto stats
if "%COMMAND%"=="setup" goto setup
if "%COMMAND%"=="help" goto help
if "%COMMAND%"=="--help" goto help
if "%COMMAND%"=="-h" goto help

echo [ERROR] Unknown command: %COMMAND%
echo.
goto help

:build
echo ================================
echo   Building Docker image...
echo ================================
docker-compose build
if %errorlevel% equ 0 (
    echo [SUCCESS] Build completed!
) else (
    echo [ERROR] Build failed!
    exit /b 1
)
goto end

:run
echo ================================
echo   Video Lesson Splitter
echo ================================
REM Check if videos_input has any videos
dir /b videos_input 2>nul | findstr "^" >nul
if %errorlevel% neq 0 (
    echo [WARNING] No videos found in videos_input/
    echo [INFO] Please add your videos to the videos_input/ directory
    exit /b 1
)
echo [INFO] Starting Video Lesson Splitter...
docker-compose run --rm video-splitter
goto end

:detached
echo ================================
echo   Starting in background...
echo ================================
docker-compose up -d
if %errorlevel% equ 0 (
    echo [SUCCESS] Container started in background
    echo [INFO] View logs with: run.bat logs
)
goto end

:logs
docker-compose logs -f --tail=100
goto end

:stop
echo ================================
echo   Stopping containers...
echo ================================
docker-compose down
if %errorlevel% equ 0 (
    echo [SUCCESS] Containers stopped
)
goto end

:clean
echo ================================
echo   Cleanup
echo ================================
echo [WARNING] This will remove all containers, volumes, and images
set /p CONFIRM="Are you sure? (y/N): "
if /i "%CONFIRM%"=="y" (
    echo [INFO] Cleaning up...
    docker-compose down -v --rmi all
    echo [SUCCESS] Cleanup completed
) else (
    echo [INFO] Cleanup cancelled
)
goto end

:shell
echo ================================
echo   Opening shell in container...
echo ================================
docker-compose run --rm video-splitter /bin/bash
goto end

:stats
docker stats video-lesson-splitter
goto end

:setup
echo ================================
echo   Setting up directories...
echo ================================
if not exist "videos_input" mkdir videos_input
if not exist "lessons_output" mkdir lessons_output
if not exist "logs" mkdir logs
echo [SUCCESS] Directories created
echo [INFO] Add your videos to: videos_input/
goto end

:help
echo ================================
echo   Video Lesson Splitter
echo ================================
echo.
echo Usage: run.bat [command]
echo.
echo Commands:
echo   build       Build Docker image
echo   run         Run the application (interactive)
echo   detached    Run in background
echo   logs        View logs
echo   stop        Stop containers
echo   clean       Remove all containers, volumes, and images
echo   shell       Open shell in container
echo   stats       Show container resource usage
echo   setup       Create necessary directories
echo   help        Show this help message
echo.
echo Examples:
echo   run.bat build          # Build the image
echo   run.bat run            # Run interactively
echo   run.bat logs           # View logs
echo.
goto end

:end
endlocal

