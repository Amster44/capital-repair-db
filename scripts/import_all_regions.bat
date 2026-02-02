@echo off
echo Importing all PFO regions...
for %%r in (02 12 13 18 21 43 52 56 58 59 63 64 73) do (
    echo.
    echo === Importing region %%r ===
    python import_csv.py --region %%r
)
echo.
echo All regions imported!
pause
