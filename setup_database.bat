@echo off
chcp 65001 >nul
echo ================================================
echo Capital Repair Database Setup
echo ================================================
echo.

REM Ask for PostgreSQL password
set /p PGPASSWORD="Enter PostgreSQL password (set during installation): "
echo.

echo Creating database...
psql -U postgres -c "CREATE DATABASE capital_repair_db ENCODING 'UTF8';" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Database created successfully
) else (
    echo [OK] Database already exists or error occurred
)
echo.

echo Applying migrations...
echo [1/2] Creating tables...
psql -U postgres -d capital_repair_db -f database\001_initial_schema.sql >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Tables created
) else (
    echo [ERROR] Failed to create tables
)

echo [2/2] Creating views and initial data...
psql -U postgres -d capital_repair_db -f database\002_views_and_data.sql >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Views created
) else (
    echo [ERROR] Failed to create views
)

echo.
echo Checking created tables...
psql -U postgres -d capital_repair_db -c "\dt" -q

echo.
echo Saving password to config.py...
powershell -Command "(Get-Content scripts\config.py) -replace \"'password': os.getenv\('DB_PASSWORD', 'your_password_here'\)\", \"'password': os.getenv('DB_PASSWORD', '%PGPASSWORD%')\" | Set-Content scripts\config.py"

echo.
echo ================================================
echo Done! Database is ready.
echo ================================================
echo.
echo Next step: run import_data.bat
echo.
pause
