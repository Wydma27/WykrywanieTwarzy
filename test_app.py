#!/usr/bin/env python3
"""Skrypt testowy - sprawdzi czy wszystkie komponenty działają"""

import sys
import cv2
from pathlib import Path

def test_opencv():
    """Test OpenCV"""
    print("[TEST 1] OpenCV...", end=" ")
    try:
        print(f"✓ (wersja {cv2.__version__})")
        return True
    except Exception as e:
        print(f"✗ BŁĄD: {e}")
        return False

def test_cascade():
    """Test cascady twarzy"""
    print("[TEST 2] Haar Cascade...", end=" ")
    try:
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        cascade = cv2.CascadeClassifier(cascade_path)
        if cascade.empty():
            print("✗ BŁĄD: Nie można załadować cascady")
            return False
        print("✓")
        return True
    except Exception as e:
        print(f"✗ BŁĄD: {e}")
        return False

def test_camera():
    """Test kamery"""
    print("[TEST 3] Kamera...", end=" ")
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("✗ BŁĄD: Kamera niedostępna")
            cap.release()
            return False
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print("✗ BŁĄD: Nie można czytać z kamery")
            return False
        
        print(f"✓ ({frame.shape[0]}x{frame.shape[1]})")
        return True
    except Exception as e:
        print(f"✗ BŁĄD: {e}")
        return False

def test_database():
    """Test bazy danych"""
    print("[TEST 4] Baza danych SQLite...", end=" ")
    try:
        from database import Database
        db = Database("test_db.db")
        
        # Spróbuj dodać wpis
        db.add_detection("test.jpg", "/path/to/test.jpg", 1, [])
        
        # Sprawdź czy się dodało
        detections = db.get_all_detections()
        
        print("✓")
        
        # Usuń testową bazę
        Path("test_db.db").unlink(missing_ok=True)
        return True
    except Exception as e:
        print(f"✗ BŁĄD: {e}")
        Path("test_db.db").unlink(missing_ok=True)
        return False

def test_tkinter():
    """Test Tkinter"""
    print("[TEST 5] Tkinter GUI...", end=" ")
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.destroy()
        print("✓")
        return True
    except Exception as e:
        print(f"✗ BŁĄD: {e}")
        return False

def test_pil():
    """Test PIL/Pillow"""
    print("[TEST 6] Pillow (obrazy)...", end=" ")
    try:
        from PIL import Image, ImageTk
        from PIL import __version__
        print(f"✓ (wersja {__version__})")
        return True
    except Exception as e:
        print(f"✗ BŁĄD: {e}")
        return False

def main():
    print("""
╔════════════════════════════════════════════╗
║  Tester Aplikacji do Detekcji Twarzy      ║
╚════════════════════════════════════════════╝
""")
    
    tests = [
        ("Python", lambda: True),
        ("OpenCV", test_opencv),
        ("Haar Cascade", test_cascade),
        ("Kamera", test_camera),
        ("Baza danych", test_database),
        ("Tkinter", test_tkinter),
        ("Pillow", test_pil),
    ]
    
    results = []
    for name, test_func in tests:
        if name != "Python":
            result = test_func()
            results.append((name, result))
    
    print(f"\n{'='*44}")
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"Wynik: {passed}/{total} testów przeszło")
    
    if passed == total:
        print("\n✓ WSZYSTKO OK! Możesz uruchomić aplikację!")
        return 0
    else:
        print("\n✗ Są błędy. Spróbuj:")
        print("  pip install --upgrade opencv-python Pillow")
        return 1

if __name__ == "__main__":
    sys.exit(main())
