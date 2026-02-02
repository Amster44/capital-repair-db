@echo off
chcp 65001 >nul
echo ================================================
echo Capital Repair Database Setup (FIXED)
echo ================================================
echo.

set /p psql_path="Enter path to PostgreSQL bin folder (e.g., C:\Program Files\PostgreSQL\16\bin): "

if not exist "%psql_path%\psql.exe" (
    echo [ERROR] psql.exe not found in specified path
    echo Please check the path and try again
    pause
    exit /b 1
)

set /p password="Enter PostgreSQL password: "

echo.
echo Creating database...
"%psql_path%\psql.exe" -U postgres -c "CREATE DATABASE capital_repair_db ENCODING 'UTF8';" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Database created successfully
) else (
    echo [OK] Database already exists or error occurred
)

echo.
echo Applying migrations...
echo [1/2] Creating tables...
"%psql_path%\psql.exe" -U postgres -d capital_repair_db -f database\001_initial_schema.sql
if %ERRORLEVEL% EQU 0 (
    echo [OK] Tables created
) else (
    echo [ERROR] Failed to create tables
    pause
    exit /b 1
)

echo [2/2] Creating views and initial data...
"%psql_path%\psql.exe" -U postgres -d capital_repair_db -f database\002_views_and_data.sql
if %ERRORLEVEL% EQU 0 (
    echo [OK] Views and data created
) else (
    echo [ERROR] Failed to create views
    pause
    exit /b 1
)

echo.
echo Checking created tables...
"%psql_path%\psql.exe" -U postgres -d capital_repair_db -c "\dt"

echo.
echo Saving password to config.py...
powershell -Command "(Get-Content scripts\config.py) -replace \"'password': '[^']*'\", \"'password': '%password%'\" | Set-Content scripts\config.py"

echo.
echo ================================================
echo Done! Database is ready.
echo ================================================
echo.
echo Next step: run import_data.bat
echo.
pause
