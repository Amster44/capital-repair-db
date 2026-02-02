@echo off
echo ================================================
echo Installation PostgreSQL 16
echo ================================================
echo.
echo Opening download page...
echo Browser will open to download PostgreSQL installer.
echo.
echo IMPORTANT during installation:
echo 1. Remember the password for user 'postgres'
echo 2. Keep port 5432 (default)
echo 3. Locale: Russian, Russia
echo.
pause

start https://www.enterprisedb.com/downloads/postgres-postgresql-downloads

echo.
echo After PostgreSQL installation:
echo 1. Restart command prompt
echo 2. Run: setup_database.bat
echo.
pause
