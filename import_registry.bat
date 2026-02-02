@echo off
chcp 65001 >nul
echo ================================================
echo Import Registry of Information Providers
echo ================================================
echo.
echo This will update management companies with contact information:
echo - Phone numbers
echo - Email addresses
echo - Director names
echo - Legal addresses
echo.
echo Source: Registry file (Реестр поставщиков информации)
echo.
pause

cd scripts

echo.
echo Importing Registry data...
python import_registry.py

cd ..

echo.
echo ================================================
echo Verification: Management Companies with Contacts
echo ================================================
echo.

psql -U postgres -d capital_repair_db -c "SELECT COUNT(*) as total, COUNT(phone) as with_phone, ROUND(COUNT(phone) * 100.0 / COUNT(*), 1) as phone_pct, COUNT(email) as with_email, ROUND(COUNT(email) * 100.0 / COUNT(*), 1) as email_pct, COUNT(director_name) as with_director, ROUND(COUNT(director_name) * 100.0 / COUNT(*), 1) as director_pct FROM management_companies;"

echo.
echo.
echo Sample of Management Companies with Full Contact Info:
echo ================================================

psql -U postgres -d capital_repair_db -c "SELECT full_name, phone, email, director_name FROM management_companies WHERE phone IS NOT NULL AND email IS NOT NULL LIMIT 5;"

echo.
echo ================================================
echo Done! Management companies updated with contacts.
echo ================================================
echo.
echo Next step: run check_data.bat to view target buildings with full UK info
echo.
pause
