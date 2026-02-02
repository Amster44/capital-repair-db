@echo off
chcp 65001 >nul
echo ================================================
echo Import OJF Data (Building-to-UK Links)
echo ================================================
echo.
echo This will link buildings to management companies (UK/TSJ/JSK)
echo using data from GIS ZKH (Housing Fund Objects)
echo.
echo Available modes:
echo [1] Only Tatarstan (for testing, ~1 minute)
echo [2] All 14 PFO regions (~10 minutes)
echo.
set /p choice="Your choice (1 or 2): "

cd scripts

if "%choice%"=="1" (
    echo.
    echo Importing OJF data for Tatarstan...
    python import_ojf.py --region 16
    echo.
    echo [OK] Tatarstan OJF import completed
) else (
    echo.
    echo Importing OJF data for all 14 PFO regions...
    echo This will process ~40 CSV files
    echo.
    python import_ojf.py --all
    echo.
    echo [OK] All regions OJF import completed
)

cd ..

echo.
echo ================================================
echo Verification: Buildings with Management Companies
echo ================================================
echo.

psql -U postgres -d capital_repair_db -c "SELECT r.region_name, COUNT(DISTINCT b.id) as total_buildings, COUNT(DISTINCT CASE WHEN b.management_company_id IS NOT NULL THEN b.id END) as linked_to_uk, ROUND(COUNT(DISTINCT CASE WHEN b.management_company_id IS NOT NULL THEN b.id END) * 100.0 / NULLIF(COUNT(DISTINCT b.id), 0), 1) as percentage FROM regions r LEFT JOIN buildings b ON r.id = b.region_id WHERE r.is_active = true GROUP BY r.region_name HAVING COUNT(b.id) > 0 ORDER BY linked_to_uk DESC;"

echo.
echo.
echo Management Companies Statistics:
echo ================================================

psql -U postgres -d capital_repair_db -c "SELECT organization_type, COUNT(*) as total FROM management_companies GROUP BY organization_type;"

echo.
echo ================================================
echo Done! Buildings are now linked to management companies.
echo ================================================
echo.
echo Next step: Import Registry data for UK contact information
echo.
pause
