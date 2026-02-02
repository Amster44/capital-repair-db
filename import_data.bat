@echo off
chcp 65001 >nul
echo ================================================
echo Data Import to Database
echo ================================================
echo.

echo Installing Python dependencies...
pip install -r requirements.txt -q
if %ERRORLEVEL% EQU 0 (
    echo [OK] Dependencies installed
) else (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo ================================================
echo Data Import by Regions
echo ================================================
echo.
echo You have data for all 14 PFO regions:
echo 1. Tatarstan (16)            8. Nizhny Novgorod (52)
echo 2. Bashkortostan (02)        9. Orenburg (56)
echo 3. Mari El (12)              10. Penza (58)
echo 4. Mordovia (13)             11. Perm (59)
echo 5. Udmurtia (18)             12. Samara (63)
echo 6. Chuvashia (21)            13. Saratov (64)
echo 7. Kirov (43)                14. Ulyanovsk (73)
echo.
echo Choose import mode:
echo [1] Only Tatarstan (for testing, ~1 minute)
echo [2] All 14 PFO regions (~15 minutes)
echo.
set /p choice="Your choice (1 or 2): "

cd scripts

if "%choice%"=="1" (
    echo.
    echo Importing Tatarstan...
    python import_csv.py --region 16
    echo.
    echo [OK] Tatarstan import completed
) else (
    echo.
    echo Importing all 14 PFO regions...
    echo.

    echo [1/14] Tatarstan...
    python import_csv.py --region 16

    echo [2/14] Bashkortostan...
    python import_csv.py --region 02

    echo [3/14] Mari El...
    python import_csv.py --region 12

    echo [4/14] Mordovia...
    python import_csv.py --region 13

    echo [5/14] Udmurtia...
    python import_csv.py --region 18

    echo [6/14] Chuvashia...
    python import_csv.py --region 21

    echo [7/14] Kirov Oblast...
    python import_csv.py --region 43

    echo [8/14] Nizhny Novgorod Oblast...
    python import_csv.py --region 52

    echo [9/14] Orenburg Oblast...
    python import_csv.py --region 56

    echo [10/14] Penza Oblast...
    python import_csv.py --region 58

    echo [11/14] Perm Krai...
    python import_csv.py --region 59

    echo [12/14] Samara Oblast...
    python import_csv.py --region 63

    echo [13/14] Saratov Oblast...
    python import_csv.py --region 64

    echo [14/14] Ulyanovsk Oblast...
    python import_csv.py --region 73

    echo.
    echo [OK] All 14 regions import completed
)

cd ..

echo.
echo ================================================
echo Data Verification
echo ================================================
echo.

psql -U postgres -d capital_repair_db -c "SELECT r.region_name, COUNT(b.id) as buildings, COUNT(l.id) as lifts FROM regions r LEFT JOIN buildings b ON r.id = b.region_id LEFT JOIN lifts l ON b.id = l.building_id WHERE r.is_active = true GROUP BY r.region_name ORDER BY buildings DESC;"

echo.
echo ================================================
echo Done! Data imported.
echo ================================================
echo.
echo Next step: run check_data.bat to view target buildings
echo.
pause
