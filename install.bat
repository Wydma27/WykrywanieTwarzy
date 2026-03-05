@echo off
echo ================================
echo Instalator - Aplikacja Detekcji Twarzy
echo ================================
echo.

echo Sprawdzanie Pythona...
python --version
if errorlevel 1 (
    echo BLAD: Python nie jest zainstalowany!
    pause
    exit /b 1
)

echo.
echo Aktualizowanie pip...
python -m pip install --upgrade pip

echo.
echo Instalowanie wymaganych pakietow...
pip install -r requirements.txt

echo.
echo ================================
echo Instalacja zakonczona!
echo ================================
echo.
echo Aby uruchomic aplikacje, wpisz:
echo   .venv\Scripts\activate
echo   python main.py
echo.
pause
