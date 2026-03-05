# 🔍 Aplikacja do Detekcji Twarzy z OpenCV

Profesjonalna aplikacja do wykrywania twarzy na zdjęciach i w transmisji z kamery internetowej, z integracją bazy danych i interfejsem graficznym.

## 📋 Funkcjonalności

- ✅ **Detekcja twarzy na zdjęciach** - wczytaj dowolne zdjęcie i automatycznie wykryj wszystkie twarze
- 📷 **Transmisja z kamery** - monitoruj twarze w czasie rzeczywistym
- 💾 **Baza danych SQLite** - wszystkie wykrycia są automatycznie zapisywane
- 📊 **Statystyki i historia** - przeglądaj dane o wykrytych twarzach
- 🎨 **Interfejs graficzny** - intuicyjny i łatwy w użyciu
- 📍 **Współrzędne twarzy** - precyzyjne lokalizacje wszystkich znalezionych twarzy

## 🛠️ Instalacja

### 1. Wymagania wstępne
- Python 3.7+
- pip (menadżer pakietów)
- Kamera internetowa (opcjonalnie, do funkcji transmisji)

### 2. Instalacja zależności

```bash
pip install -r requirements.txt
```

Pakiety:
- `opencv-python` - OpenCV do przetwarzania obrazu
- `Pillow` - do wyświetlania obrazów w GUI

## 🚀 Uruchomienie aplikacji

### Na Windows:
```bash
.venv\Scripts\activate
python main.py
```

### Na macOS/Linux:
```bash
source .venv/bin/activate
python main.py
```

Aplikacja uruchomi się z graficznym interfejsem użytkownika.

## 📖 Instrukcja obsługi

### Wczytaj Zdjęcie
1. Kliknij przycisk **"📁 Wczytaj Zdjęcie"**
2. Wybierz plik zdjęcia (JPG, PNG, BMP)
3. Aplikacja automatycznie:
   - Wykryje wszystkie twarze
   - Narysuje prostokąty wokół znalezionych twarzy
   - Zapisze wynik z zaznaczeniami
   - Doda informacje do bazy danych

### Włącz Kamerę
1. Kliknij **"📷 Włącz Kamerę"**
2. Transmisja z kamery będzie wyświetlana w czasie rzeczywistym
3. Naciśnij klawisz **'S'** aby zrobić zdjęcie i zapisać go
4. Kliknij przycisk ponownie aby wyłączyć kamerę

### Historia
1. Kliknij **"📊 Historia"**
2. Pokaże się lista wszystkich przeanalizowanych zdjęć
3. Możesz usunąć wpisy z bazy danych

### Statystyki
1. Kliknij **"📈 Statystyki"**
2. Pokaże się:
   - Liczba przeanalizowanych zdjęć
   - Liczba wykrytych twarzy
   - Średnia liczba twarzy na zdjęcie

## 📂 Struktura projektu

```
WykrywanieTwarzy/
├── main.py                 # Główna aplikacja GUI
├── database.py             # Moduł bazy danych
├── face_detector.py        # Moduł detekcji twarzy
├── requirements.txt        # Zależności
├── face_detection.db       # Baza danych (tworzy się automatycznie)
└── detected_faces/         # Folder na zapisane zdjęcia (tworzy się automatycznie)
```

## 🗄️ Baza danych

Aplikacja automatycznie tworzy bazę SQLite z dwoma tabelami:

### Tabela `faces`
- `id` - unikalny identyfikator
- `image_name` - nazwa zdjęcia
- `image_path` - ścieżka do zdjęcia
- `num_faces` - liczba znalezionych twarzy
- `detection_date` - data i czas detekcji
- `face_coordinates` - współrzędne twarzy (JSON)

### Tabela `statistics`
- Przechowuje statystyki (dla przyszłych rozszerzeń)

## 🎯 Algorytm detekcji

Aplikacja używa **Haar Cascades** - klasycznego, ale niezawodnego algorytmu do detekcji twarzy:
- Szybkie przetwarzanie
- Niska złożoność obliczeniowa
- Dobra dokładność dla frontalnych widoków twarzy

## 📝 Parametry detekcji

W pliku `face_detector.py` można dostosować czułość detekcji:

```python
faces = self.face_cascade.detectMultiScale(
    gray,
    scaleFactor=1.1,      # Im mniejsza, tym pewniejsza detekcja (wolniej)
    minNeighbors=5,       # Im wyżej, tym mniej fałszywych pozytywów
    minSize=(30, 30)      # Minimalny rozmiar twarzy
)
```

## 🔧 Troubleshooting

### Kamera nie działa
- Sprawdź czy kamera jest podłączona
- Zmień numer kamery w `camera_loop()` (0 = domyślna kamera)
- Sprawdź uprawnienia dostępu do kamery

### Brak OpenCV
```bash
pip install --upgrade opencv-python
```

### Problem z wyświetlaniem
Upewnij się że masz zainstalowany Pillow:
```bash
pip install --upgrade Pillow
```

## 📌 Wskazówki

- Dla najlepszych rezultatów, zdjęcia powinny mieć jasne oświetlenie
- Twarze skierowane frontalnie są wykrywane najlepiej
- W ostrym świetle słonecznym detekcja może być mniej dokładna
- Możesz ręcznie dostosować parametry `scaleFactor` i `minNeighbors` dla swoich potrzeb

## 🚀 Możliwe rozszerzenia

- Rozpoznawanie emocji
- Identyfikacja osób (face recognition)
- Liczenie osób w nagraniu
- Export wyników do CSV/PDF
- Obsługa wielu formatów wideo
- Synchronizacja z chmurą

## 📄 Licencja

Projekt na licencji MIT

## 👨‍💻 Autor

Aplikacja do detekcji twarzy zbudowana z OpenCV

---

**Śmiało konfiguruj i rozszerzaj aplikację do swoich potrzeb!** 🎉
