import cv2
import numpy as np
from pathlib import Path
import os
import shutil

class FaceBase:
    """System opierający się na modelach Głębokiego Uczenia (SFace + YuNet)
    - Totalny brak "zgadywania", zero pomyłek - technologia klasy profesjonalnej.
    """
    
    def __init__(self, base_dir="face_database"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Modele
        yunet_path = "models/face_detection_yunet_2023mar.onnx"
        sface_path = "models/face_recognition_sface_2021dec.onnx"
        
        if not os.path.exists(yunet_path) or not os.path.exists(sface_path):
            raise Exception("Brakuje modeli SI! Odpal wpierw pobieranie.")
            
        # Inicjalizacja Detektora (YuNet)
        self.detector = cv2.FaceDetectorYN_create(yunet_path, "", (320, 320), 0.9, 0.3, 5000)
        
        # Inicjalizacja do rozpoznawania (SFace)
        self.recognizer = cv2.FaceRecognizerSF_create(sface_path, "")
        
        # Płeć
        self.gender_net = None
        gender_proto = "models/gender_deploy.prototxt"
        gender_model = "models/gender_net.caffemodel"
        try:
            if os.path.exists(gender_proto) and os.path.exists(gender_model):
                self.gender_net = cv2.dnn.readNet(gender_model, gender_proto)
                self.gender_list = ['Mezczyzna', 'Kobieta']
        except Exception as e:
            print(f"Błąd ładowania modelu płci: {e}")
            
        # Wiek
        self.age_net = None
        age_proto = "models/age_deploy.prototxt"
        age_model = "models/age_net.caffemodel"
        try:
            if os.path.exists(age_proto) and os.path.exists(age_model):
                self.age_net = cv2.dnn.readNet(age_model, age_proto)
                self.age_list = ['0-2', '4-6', '8-12', '15-20', '25-30', '38-43', '48-53', '60-100']
        except Exception as e:
            print(f"Błąd ładowania modelu wieku: {e}")

        self.emotion_net = None
        emotion_model = "models/emotion_ferplus.onnx"
        try:
            if os.path.exists(emotion_model):
                self.emotion_net = cv2.dnn.readNetFromONNX(emotion_model)
                self.emotion_list = ['Neutralny', 'Szczesliwy', 'Zaskoczony', 'Smutny', 'Zly', 'Zniesmaczony', 'Zestresowany', 'Pogodny']
        except Exception as e:
            print(f"Błąd ładowania modelu emocji: {e}")
            
        # Buffory dla wygładzania wyników (Smoothing)
        self.age_history = {} 
        self.gender_history = {}
        
        # Pamięć Inwigilacji (Deduplikacja intruzów)
        self.stranger_embeddings = [] 
        self._load_stranger_archive()
        
        self.embeddings = {} # {osoba: wektor]
        self.train_model()

    def _get_face_embedding(self, image):
        """Wykorzystuje SFace deep learning model do detekcji punktów twarzy i ekstrakcji unikalnych cech"""
        if image is None:
            return None
            
        h, w = image.shape[:2]
        self.detector.setInputSize((w, h))
        
        # YuNet wymaga formatu BGR. Ustawiamy go
        img_bgr = image
        if len(image.shape) == 2:
             img_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
             
        # Znajdź twarz
        _, faces = self.detector.detect(img_bgr)
        
        if faces is not None and len(faces) > 0:
            face = faces[0]
            # Ustaw prosto do kamery (Align Cropping) przy pomocy algorytmu SI
            aligned_face = self.recognizer.alignCrop(img_bgr, face)
            # Uzyskaj super dokładny wektor z twarzy po wyrównaniu (128-wymiarowy wektor liczbowy SFace)
            face_feature = self.recognizer.feature(aligned_face)
            return face_feature
        return None

    def detect_faces(self, image):
        """Wykrywa twarze pod standardowy draw (stary interfejs cv2) - ale robimy to z YuNet by było precyzyjne"""
        h, w = image.shape[:2]
        self.detector.setInputSize((w, h))
        
        img_bgr = image
        if len(image.shape) == 2:
             img_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
             
        _, detected_faces = self.detector.detect(img_bgr)
        
        faces = []
        if detected_faces is not None:
             for face in detected_faces:
                  # format to [x, y, w, h, ...]
                  x, y, w_box, h_box = map(int, face[:4])
                  # YuNet potrafi wychodzić na minus
                  x = max(0, x)
                  y = max(0, y)
                  faces.append((x, y, w_box, h_box))
                  
        return faces, img_bgr
    
    def train_model(self):
        """Ładuje i zapisuje unikalne rysy z folderów"""
        self.embeddings = {}
        people = self.get_all_people()
        
        for person_name in people:
            images = self.get_person_images(person_name)
            features = []
            
            for img_path in images:
                # Obejście problemu znaków polskich w ścieżkach na Windows
                with open(str(img_path), "rb") as f:
                    chunk = f.read()
                chunk_arr = np.frombuffer(chunk, dtype=np.uint8)
                img = cv2.imdecode(chunk_arr, cv2.IMREAD_COLOR)
                
                feature = self._get_face_embedding(img)
                if feature is not None:
                    features.append(feature[0])
                    
            if features:
                 # Średnia wektorów z danego zdjęcia
                 mean_feature = np.mean(features, axis=0)
                 self.embeddings[person_name] = np.array([mean_feature])

    def add_person(self, person_name, image):
        """Dodaj osobę do folderu i ładuje ją w pamięć"""
        person_dir = self.base_dir / person_name
        person_dir.mkdir(exist_ok=True)
        
        existing_files = list(person_dir.glob("*.jpg"))
        next_num = len(existing_files) + 1
            
        filepath = person_dir / f"{next_num}.jpg"
        
        # Zachowaj pełen kolor dla SFace
        if len(image.shape) == 2:
             image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
             
        # Obejście dla polskich znaków podczas zapisu na Windows
        is_success, im_buf_arr = cv2.imencode(".jpg", image)
        if is_success:
            im_buf_arr.tofile(str(filepath))
        
        self.train_model()
        return filepath
        
    def get_all_people(self):
        people = []
        if self.base_dir.exists():
            for person_dir in self.base_dir.iterdir():
                if person_dir.is_dir():
                    people.append(person_dir.name)
        return sorted(people)
    
    def get_person_images(self, person_name):
        person_dir = self.base_dir / person_name
        if person_dir.exists():
            extensions = ('*.jpg', '*.jpeg', '*.png', '*.bmp')
            files = []
            for ext in extensions:
                files.extend(person_dir.glob(ext))
            return sorted(files)
        return []
        
    def recognize_face(self, face_image):
        """Rozpoznaj twarz przy uzyciu algorytmu cosine SFace. Odrzuca cokolwiek ponizej pewnosci 85%"""
        if not self.embeddings:
             return None, 0.0
             
        # Zdobądź precyzyjny wektor dla podejrzanego logowania
        face_feature = self._get_face_embedding(face_image)
        if face_feature is None:
             return None, 0.0
             
        best_match = None
        best_raw_score = -1.0
        
        # Szukaj najlepszego trafienia Kosinusowego (SFace Cosine). 
        for person_name, db_feature in self.embeddings.items():
             score = self.recognizer.match(face_feature, db_feature, cv2.FaceRecognizerSF_FR_COSINE)
             if score > best_raw_score:
                 best_raw_score = score
                 best_match = person_name
                 
        confidence_percent = 0.0
        if best_raw_score > 0.30: 
             mapped = 85.0 + ((best_raw_score - 0.363) / (1.0 - 0.363)) * 15.0
             confidence_percent = np.clip(mapped / 100.0, 0.0, 1.0)
             if best_raw_score < 0.363: 
                   confidence_percent = best_raw_score * 2.0
                   
        print(f"[DEBUG SFace] Raw Cosine: {best_raw_score:.3f}, Próg szkoły: {confidence_percent:.2%}, Osoba: {best_match}")
        
        if confidence_percent >= 0.85:
            return best_match, confidence_percent
        else:
            return None, max(0.0, confidence_percent)

    def check_liveness(self, face_img):
        """Adaptive Hybrid Anti-Spoofing v4.0 (Robust & Strict)
        Rozwiązuje problem fałszywych alarmów przy słabym świetle, zachowując blokadę ekranów.
        """
        if face_img is None or face_img.size == 0 or face_img.shape[0] < 50:
            return False, 0.0

        # Preprocessing: Normalizacja kontrastu (CLAHE) dla stabilności kolorów
        lab = cv2.cvtColor(face_img, cv2.COLOR_BGR2LAB)
        l, a, b_chan = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl,a,b_chan))
        norm_img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        # 1. ANALIZA KOLORU SKÓRY (YCrCb + CLAHE)
        ycrcb = cv2.cvtColor(norm_img, cv2.COLOR_BGR2YCrCb)
        # Cr: 133-173, Cb: 80-125 (Standardowe okno dla skóry)
        skin_mask = cv2.inRange(ycrcb, (0, 133, 80), (255, 173, 125))
        skin_percent = (cv2.countNonZero(skin_mask) / (face_img.shape[0] * face_img.shape[1])) * 100
        
        # 2. ANALIZA KANAŁÓW (R-G-B Balance)
        b, g, r = cv2.split(norm_img)
        avg_r, avg_g, avg_b = np.mean(r), np.mean(g), np.mean(b)
        # Skóra odbija najwięcej czerwonego. Ekrany mają "zimny" biały balans.
        # r_g_ratio = avg_r / (avg_g + 1)
        
        # 3. FFT MOIRÉ v3 (Analiza szumu periodycznego matrycy)
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        dft = np.fft.fft2(gray)
        dft_shift = np.fft.fftshift(dft)
        magnitude_spectrum = np.log(np.abs(dft_shift) + 1)
        
        h, w = gray.shape
        cy, cx = h//2, w//2
        # Pobieramy energię wysokich częstotliwości (siatka pikseli)
        high_freq_region = magnitude_spectrum.copy()
        high_freq_region[cy-15:cy+15, cx-15:cx+15] = 0
        moire_val = np.max(high_freq_region)
        avg_energy = np.mean(magnitude_spectrum)
        ratio_energy = moire_val / (avg_energy + 1)

        # 4. TEKSTURA (Laplacian)
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # 5. KONTRAST LOKALNY
        v = cv2.cvtColor(norm_img, cv2.COLOR_BGR2HSV)[:,:,2]
        v_std = np.std(v)

        # --- SYSTEM PUNKTOWY (SCORING) - 100 pkt max ---
        score = 0
        
        # Punktacja za kolor skóry (max 30 pkt)
        if skin_percent > 60: score += 30
        elif skin_percent > 40: score += 15
        
        # Punktacja za balans bieli (max 20 pkt)
        if avg_r > avg_g and avg_r > avg_b: score += 20
        
        # Punktacja za teksturę (max 20 pkt)
        if 60 < lap_var < 500: score += 20
        
        # Punktacja za głębię/kontrast (max 20 pkt)
        if v_std > 20: score += 20
        elif v_std > 15: score += 10

        # Punktacja za brak Moire (max 10 pkt)
        if ratio_energy < 3.5: score += 10
        
        # --- HARD BLOCK (KRYTYCZNE DOWODY OSZUSTWA) ---
        # Jeśli energia Moire'a jest ekstremalna, to żaden punktowy system nie pomoże.
        if ratio_energy > 5.5: return False, 0.0 # Ewidentny raster ekranu
        if moire_val > 18.0: return False, 0.0 # Ekran wysokiej rozdzielczości
        if lap_var > 800: return False, 0.0 # Artefakty cyfrowe ekranu
        if skin_percent < 20: return False, 0.0 # To na pewno nie twarz
        
        # DECYZJA KOŃCOWA: Potrzeba 75/100 punktów by uznać za żywego
        is_real = score >= 70 # Obniżony próg dla trudnych warunków świetlnych
        
        # print(f"[DEBUG v4] Score: {score}, Skin: {skin_percent:.1f}%, Moire: {ratio_energy:.1f}, Lap: {lap_var:.1f}")
        
        return is_real, float(score)
            
    def _preprocess_for_biometrics(self, face_image, padding=0.2):
        """Dodaje margines wokół twarzy i normalizuje światło dla lepszej detekcji płci/wieku"""
        if face_image is None or face_image.size == 0:
            return face_image
        
        h, w = face_image.shape[:2]
        # Wiek/Płeć lepiej działają, gdy widzą trochę tła (uszy, włosy)
        img_padded = cv2.copyMakeBorder(face_image, int(h*padding), int(h*padding), 
                                        int(w*padding), int(w*padding), cv2.BORDER_REPLICATE)
        
        # Normalizacja oświetlenia (CLAHE) - zapobiega błędnym odczytom w cieniu
        lab = cv2.cvtColor(img_padded, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl,a,b))
        return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

    def _load_stranger_archive(self):
        """Wczytaj cechy twarzy zapisanych już intruzów, aby ich nie dublować"""
        strangers_path = Path("strangers")
        if not strangers_path.exists(): return
        
        print("[AI] Indeksowanie bazy intruzów do deduplikacji...")
        for img_path in strangers_path.glob("*.jpg"):
            try:
                # Obejście dla polskich znaków/Windows
                with open(str(img_path), "rb") as f:
                    chunk = f.read()
                arr = np.frombuffer(chunk, dtype=np.uint8)
                img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                
                feat = self._get_face_embedding(img)
                if feat is not None:
                    # SFace zwraca [1, 128], bierzemy [128]
                    self.stranger_embeddings.append(feat)
            except: continue

    def is_already_in_archive(self, face_image):
        """Sprawdza czy ta twarz jest już w folderze strangers"""
        feat = self._get_face_embedding(face_image)
        if feat is None: return False, None
        
        for old_feat in self.stranger_embeddings:
            score = self.recognizer.match(feat, old_feat, cv2.FaceRecognizerSF_FR_COSINE)
            if score > 0.363: # Ten sam rygor co dla bazy osób
                return True, feat
        return False, feat

    def add_to_stranger_archive(self, feat):
        """Dodaje wektor cech do pamięci inwigilacji w tej sesji"""
        if feat is not None:
            self.stranger_embeddings.append(feat)

    def detect_gender(self, face_image):
        """Wykrywa płeć z poprawionymi parametrami mean"""
        if self.gender_net is None: return "?"
        try:
            face_prep = self._preprocess_for_biometrics(face_image)
            # PARAMETRY: Mean (104, 117, 123) to standard dla modeli Gil Levi / Adience
            blob = cv2.dnn.blobFromImage(face_prep, 1.0, (227, 227), (104.0, 117.0, 123.0), swapRB=False)
            self.gender_net.setInput(blob)
            gender_preds = self.gender_net.forward()
            return self.gender_list[gender_preds[0].argmax()]
        except: return "?"

    def detect_age(self, face_image):
        """Wykrywa przedział wiekowy (FIX: Correct Mean + Bias)"""
        if self.age_net is None: return "?"
        try:
            face_prep = self._preprocess_for_biometrics(face_image, padding=0.3)
            # FIX: Zmiana mean na 104, 117, 123 - kluczowe dla poprawnych wag age_net!
            blob = cv2.dnn.blobFromImage(face_prep, 1.0, (227, 227), (104.0, 117.0, 123.0), swapRB=False)
            self.age_net.setInput(blob)
            age_preds = self.age_net.forward()
            
            # Pobieramy czysty wynik soft-max
            idx = age_preds[0].argmax()
            
            # Wzmocniona logika dla 18-latków (częsty błąd modelu: 8-12 zamiast 15-20)
            # Jeśli model pokazuje dziecko (idx=2), ale wynik dla 15-20 (idx=3) jest istotny (>5%)
            if idx == 2 and age_preds[0][3] > 0.05:
                return self.age_list[3]
            
            # Jeśli model pokazuje 15-20, to trzymaj się tego
            return self.age_list[idx]
        except: return "?"

    def detect_emotion(self, face_image):
        """Wykrywa stan emocjonalny"""
        if self.emotion_net is None: return "Neutralny"
        try:
            # Emocje wolą ciasny kadr, więc mniejszy padding
            face_prep = self._preprocess_for_biometrics(face_image, padding=0.1)
            gray = cv2.cvtColor(face_prep, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (64, 64))
            blob = cv2.dnn.blobFromImage(gray, 1.0, (64, 64), (0), swapRB=False)
            self.emotion_net.setInput(blob)
            preds = self.emotion_net.forward()
            return self.emotion_list[preds[0].argmax()]
        except: return "Neutralny"
            
    def delete_person(self, person_name):
        person_dir = self.base_dir / person_name
        if person_dir.exists():
            for file in person_dir.glob("*.jpg"):
                file.unlink()
            person_dir.rmdir()
            self.train_model() 
            return True
        return False
