#!/usr/bin/env python3
"""Skrypt instalacyjny i uruchamiający aplikację"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Uruchom polecenie i pokaż status"""
    print(f"[*] {description}...", end=" ", flush=True)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("✓")
        return True
    else:
        print("✗")
        print(result.stderr)
        return False

def main():
    print("""
╔════════════════════════════════════════╗
║   🔍 Aplikacja do Detekcji Twarzy    ║
╚════════════════════════════════════════╝
""")
    
    venv_path = Path(".venv")
    
    # 1. Utwórz venv jeśli nie istnieje
    if not venv_path.exists():
        if not run_command(f"{sys.executable} -m venv .venv", "Tworzenie wirtualnego środowiska"):
            print("❌ Błąd podczas tworzenia środowiska!")
            sys.exit(1)
    else:
        print("[✓] Środowisko już istnieje")
    
    # 2. Określ ścieżkę do pip
    if sys.platform == "win32":
        pip_exe = venv_path / "Scripts" / "pip.exe"
        python_exe = venv_path / "Scripts" / "python.exe"
    else:
        pip_exe = venv_path / "bin" / "pip"
        python_exe = venv_path / "bin" / "python"
    
    # 3. Zainstaluj zależności
    print(f"[*] Instalowanie zależności...", end=" ", flush=True)
    result = subprocess.run(
        f'"{pip_exe}" install -r requirements.txt',
        shell=True,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✓")
    else:
        print("✗")
        print(result.stderr)
        sys.exit(1)
    
    # 4. Uruchom aplikację
    print("\n[*] Uruchamianie aplikacji...\n")
    result = subprocess.run(f'"{python_exe}" main.py', shell=True)
    
    print("\n✓ Aplikacja zamknięta.")
    return result.returncode

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠ Przerwano przez użytkownika")
        sys.exit(1)
