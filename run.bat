@echo off
chcp 65001 > nul
title Aplikacja do Detekcji Twarzy

echo.
echo =====================================
echo  🔍 Aplikacja do Detekcji Twarzy
echo =====================================
echo.

if not exist ".venv" (
    echo [1] Tworzenie wirtualnego środowiska...
    python -m venv .venv
    if errorlevel 1 (
        echo BŁĄD: Nie można utworzyć venv
        pause
        exit /b 1
    )
    echo ✓ Środowisko utworzone
    echo.
)

echo [2] Aktywowanie środowiska...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo BŁĄD: Nie można aktywować venv
    pause
    exit /b 1
)
echo ✓ Środowisko aktywne
echo.

echo [3] Sprawdzenie pakietów...
pip show opencv-python > nul 2>&1
if errorlevel 1 (
    echo Instalowanie zależności... (to może chwilę potrwać)
    pip install -r requirements.txt
    if errorlevel 1 (
        echo BŁĄD: Instalacja nie powiodła się
        pause
        exit /b 1
    )
    echo ✓ Zależności zainstalowane
) else (
    echo ✓ Wszystkie pakiety już zainstalowane
)
echo.

echo [4] Uruchamianie aplikacji...
echo.
python main.py

echo.
echo Aplikacja zamknięta.
pause
