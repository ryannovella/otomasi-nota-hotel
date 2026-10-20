@echo off
title Otomasi Nota Hotel - BPPW Jateng
cd /d "%~dp0"
echo ========================================================
echo        OTOMASI NOTA HOTEL - BPPW JAWA TENGAH
echo ========================================================
echo Sedang menyiapkan antarmuka aplikasi...
python app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Membuka aplikasi via web browser default...
    python app.py --browser
)
