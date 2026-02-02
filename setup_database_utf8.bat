@echo off
chcp 65001 >nul
echo ================================================
echo Capital Repair Database Setup (UTF-8 FIX)
echo ================================================
echo.

set PGCLIENTENCODING=UTF8
set psql_path=C:\Program Files\PostgreSQL\18\bin

echo Creating database...
"%psql_path%\psql.exe" -U postgres -c "CREATE DATABASE capital_repair_db ENCODING 'UTF8';" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Database created successfully
) else (
    echo [OK] Database already exists
)

echo.
echo Dropping existing tables (clean start)...
"%psql_path%\psql.exe" -U postgres -d capital_repair_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

echo.
echo Applying migrations with UTF-8 encoding...
echo [1/2] Creating tables...
"%psql_path%\psql.exe" -U postgres -d capital_repair_db -v ON_ERROR_STOP=1 -f database\001_initial_schema.sql
if %ERRORLEVEL% EQU 0 (
    echo [OK] Tables created
) else (
    echo [ERROR] Failed to create tables
    pause
    exit /b 1
)

echo [2/2] Creating views and initial data...
"%psql_path%\psql.exe" -U postgres -d capital_repair_db -v ON_ERROR_STOP=1 -f database\002_views_and_data.sql
if %ERRORLEVEL% EQU 0 (
    echo [OK] Views and data created
) else (
    echo [ERROR] Failed to create views
    pause
    exit /b 1
)

echo.
echo Checking created tables...
"%psql_path%\psql.exe" -U postgres -d capital_repair_db -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"

echo.
echo Counting tables...
"%psql_path%\psql.exe" -U postgres -d capital_repair_db -c "SELECT COUNT(*) as total_tables FROM information_schema.tables WHERE table_schema = 'public';"

echo.
echo Saving password to config.py...
powershell -Command "(Get-Content scripts\config.py) -replace \"'password': '[^']*'\", \"'password': '123456'\" | Set-Content scripts\config.py"

echo.
echo ================================================
echo Done! Database is ready.
echo ================================================
echo.
echo Next step: run import_data.bat
echo.
pause
