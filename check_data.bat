@echo off
chcp 65001 >nul
echo ================================================
echo Imported Data Verification
echo ================================================
echo.

echo [1] Regional Statistics
echo ================================================
psql -U postgres -d capital_repair_db -c "SELECT r.region_name, COUNT(DISTINCT b.id) as buildings, COUNT(DISTINCT CASE WHEN b.spec_account_owner_type IN ('UK', 'TSJ', 'JSK') THEN b.id END) as spec_accounts, COUNT(l.id) as lifts, COALESCE(SUM(b.overhaul_funds_balance), 0)::bigint as total_balance FROM regions r LEFT JOIN buildings b ON r.id = b.region_id LEFT JOIN lifts l ON b.id = l.building_id GROUP BY r.region_name HAVING COUNT(b.id) > 0 ORDER BY COUNT(b.id) DESC;"

echo.
echo.
echo [2] Top-20 Target Buildings (HIGH priority)
echo ================================================
psql -U postgres -d capital_repair_db -c "SELECT address, region_name, overhaul_funds_balance::bigint as balance, lifts_count, years_to_replacement, priority FROM v_target_buildings WHERE priority = 'HIGH' LIMIT 20;"

echo.
echo.
echo [3] Special Account Types Statistics
echo ================================================
psql -U postgres -d capital_repair_db -c "SELECT CASE spec_account_owner_type WHEN 'UK' THEN 'Management Company' WHEN 'TSJ' THEN 'HOA' WHEN 'JSK' THEN 'Housing Coop' WHEN 'REGOP' THEN 'Regional Operator' END as type, COUNT(*) as buildings, SUM(overhaul_funds_balance)::bigint as total_balance, AVG(overhaul_funds_balance)::bigint as avg_balance FROM buildings WHERE spec_account_owner_type IS NOT NULL GROUP BY spec_account_owner_type ORDER BY COUNT(*) DESC;"

echo.
echo.
echo [4] Lifts Requiring Replacement in Next 3 Years
echo ================================================
psql -U postgres -d capital_repair_db -c "SELECT b.address, r.region_name, COUNT(l.id) as lifts, MIN(l.decommissioning_date) as replacement_date, EXTRACT(YEAR FROM MIN(l.decommissioning_date))::int - EXTRACT(YEAR FROM CURRENT_DATE)::int as years_left FROM lifts l JOIN buildings b ON l.building_id = b.id JOIN regions r ON b.region_id = r.id WHERE l.decommissioning_date < CURRENT_DATE + INTERVAL '3 years' AND b.spec_account_owner_type IN ('UK', 'TSJ', 'JSK') GROUP BY b.id, b.address, r.region_name ORDER BY MIN(l.decommissioning_date) LIMIT 20;"

echo.
echo.
echo ================================================
echo.
pause
