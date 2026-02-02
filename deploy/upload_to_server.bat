@echo off
REM Upload Capital Repair Database to server

SET SERVER=root@62.113.36.101
SET REMOTE_DIR=/opt/capital-repair-db

echo ========================================
echo Uploading files to server...
echo ========================================

REM Create remote directory
ssh %SERVER% "mkdir -p %REMOTE_DIR%"

REM Upload project files (excluding data and venv)
echo Uploading scripts...
scp -r scripts %SERVER%:%REMOTE_DIR%/

echo Uploading web app...
scp -r app %SERVER%:%REMOTE_DIR%/

echo Uploading frontend...
scp -r frontend %SERVER%:%REMOTE_DIR%/

echo Uploading deployment scripts...
scp deploy/setup_server.sh %SERVER%:%REMOTE_DIR%/
scp deploy/config_production.py %SERVER%:%REMOTE_DIR%/scripts/config.py

echo Uploading requirements...
echo flask > requirements.txt
echo flask-cors >> requirements.txt
echo psycopg2-binary >> requirements.txt
echo pandas >> requirements.txt
echo openpyxl >> requirements.txt
echo gunicorn >> requirements.txt
scp requirements.txt %SERVER%:%REMOTE_DIR%/

echo.
echo ========================================
echo Upload completed!
echo ========================================
echo.
echo Next: Run setup_server.sh on the server
echo   ssh %SERVER%
echo   cd %REMOTE_DIR%
echo   chmod +x setup_server.sh
echo   ./setup_server.sh
echo.
