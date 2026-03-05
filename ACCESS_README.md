# 🚪 System Kontroli Dostępu - Rozpoznawanie Twarzy

Prosty system biometryczny oparty na zdjęciach w folderze.

## 🚀 Uruchomienie

```batch
Kliknij 2x: access.bat
```

Lub w terminalu:
```bash
python access_simple.py
```

## 📋 Jak to działa

### 1️⃣ **Dodaj Osobę** ➕

1. Kliknij "➕ DODAJ OSOBĘ"
2. Wpisz imię (np. "Jakub")
3. Stań przed kamerą
4. Naciśnij **SPACJA** aby zapisać twarz
5. ✅ Osoba dodana do folderu `face_database/Jakub/`

### 2️⃣ **Skanuj Twarz** 🔍

1. Kliknij "🔍 SKANUJ TWARZ"
2. Stań przed kamerą
3. System porównuje twoją twarz z bazą:
   - ✅ **DOSTĘP PRZYZNANY** - jesteś w bazie (zielenogniehty)
   - ❌ **DOSTĘP ODMÓWIONY** - nieznajna osoba (czerwony)

### 3️⃣ **Zarządzaj** 📋

- **"📋 LISTA OSÓB"** - pokaż osoby, usuń z bazy
- **"📊 HISTORIA"** - logi dostępu

## 📁 Struktura Folderów

```
face_database/
├── Jakub/
│   ├── 1.jpg
│   ├── 2.jpg
│   └── 3.jpg
├── Agata/
│   ├── 1.jpg
│   └── 2.jpg
└── Piotr/
    └── 1.jpg
```

Każdy folder = jedna osoba
Każde zdjęcie = jej twarz do porównania

## ⚙️ Jak to działa wewnątrz

1. **Dodawanie**: Nagrywasz twarz → zapisuje się w folderze osoby
2. **Skanowanie**: 
   - Bierze zdjęcie z kamery
   - Oblicza histogram twarzy (embedding)
   - Porównuje z średnim histogramem każdej osoby
   - Jeśli wystarczająco podobne → dostęp przyznany

## 💡 Wskazówki

✓ Dobre oświetlenie  
✓ Twarz skierowana prosto do kamery  
✓ Im więcej zdjęć osoby, tym lepsze rozpoznawanie  
✓ Dodaj zdjęcia z różnych kątów i warunków  

## 🔧 Parametry (można zmienić)

W `face_base.py`, funkcja `recognize_face()`:

```python
threshold=0.5  # Im wyżej, tym bardziej rygorystyczne
```

## 📸 Pierwsza konfiguracja

1. Uruchom `access.bat`
2. Dodaj kilka osób (minimum 2-3)
3. Każda osoba → nagrań 1-2 zdjęcia
4. Testuj skanowanie

## 🗑️ Usuwanie Osoby

1. Kliknij "📋 LISTA OSÓB"
2. Wybierz osobę
3. Kliknij "🗑️ USUŃ WYBRANĄ"
4. Folder kasuje się automatycnie

---

**Proste, bezpieczne i niezawodne!** ✨
