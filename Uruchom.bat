@echo off
chcp 65001 > nul
title Aplikacja do Detekcji i Rozpoznawania Twarzy
color 0A

echo.
echo ============================================================
echo   🔍 SYSTEM WIZYJNY - DETEKCJA I ROZPOZNAWANIE TWARZY
echo ============================================================
echo.

REM 1. Sprawdzenie Pythona
python --version > nul 2>&1
if errorlevel 1 (
    color 0C
    echo [BŁĄD] Python nie jest zainstalowany!
    echo Proszę pobrać Pythona z https://www.python.org/
    pause
    exit /b 1
)

REM 2. Środowisko Wirtualne (.venv)
if not exist ".venv" (
    echo [*] Tworzenie wirtualnego środowiska...
    python -m venv .venv
)

echo [*] Aktywowanie środowiska...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    color 0C
    echo [BŁĄD] Nie można aktywować .venv
    pause
    exit /b 1
)

REM 3. Instalacja/Aktualizacja zależności
echo [*] Sprawdzanie i instalowanie bibliotek (może to chwilę potrwać)...
python -m pip install --upgrade pip > nul
pip install -q -r requirements.txt
if errorlevel 1 (
    color 0C
    echo [BŁĄD] Instalacja bibliotek nie powiodła się.
    echo Sprawdź połączenie z internetem.
    pause
    exit /b 1
)

echo [OK] Wszystko gotowe!
echo.

:menu
cls
echo ============================================================
echo   WYBIERZ PROGRAM DO URUCHOMIENIA:
echo ============================================================
echo.
echo   [1] GŁÓWNA DETEKCJA TWARZY (Wykrywanie na żywo/zdjęcia)
echo   [2] SYSTEM KONTROLI DOSTĘPU (Rozpoznawanie osób)
echo   [3] LOGI I HISTORIA (Logi kogoś wykryło, kiedy kto)
echo   [4] WYJŚCIE
echo.
echo ============================================================
set /p choice="Wybierz opcję [1-4]: "

if "%choice%"=="1" goto main_app
if "%choice%"=="2" goto access_app
if "%choice%"=="3" goto logs_app
if "%choice%"=="4" exit
goto menu

:main_app
echo.
echo [*] Uruchamianie Detekcji Twarzy w nowym oknie...
start python main.py
goto menu

:access_app
echo.
echo [*] Uruchamianie Kontroli Dostępu w nowym oknie...
start python access_simple.py
goto menu

:logs_app
echo.
echo [*] Uruchamianie Panelu Logów w nowym oknie...
start python logs_app.py
goto menu

:end
echo.
echo Powrót do menu...
pause
goto menu
