@echo off
echo ============================================
echo Capital Repair DB - Upload to Server
echo ============================================
echo.
echo Server: root@62.113.36.101
echo Password: j4eVZ-g@aPA2U6
echo.
echo Uploading files...
echo.

REM Upload main directories
echo [1/5] Uploading scripts...
scp -r scripts root@62.113.36.101:/opt/capital-repair-db/

echo [2/5] Uploading backend...
scp -r backend root@62.113.36.101:/opt/capital-repair-db/

echo [3/5] Uploading frontend...
scp -r frontend root@62.113.36.101:/opt/capital-repair-db/

echo [4/5] Uploading deploy files...
scp -r deploy root@62.113.36.101:/opt/capital-repair-db/

echo [5/5] Uploading production config...
scp deploy\config_production.py root@62.113.36.101:/opt/capital-repair-db/scripts/config.py

echo.
echo ============================================
echo Upload completed!
echo ============================================
echo.
echo Next steps:
echo 1. Open deploy\QUICK_START.md
echo 2. Follow instructions starting from Step 3
echo.
pause
