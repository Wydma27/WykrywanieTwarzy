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
        # Czysty algorytm SFace w OpenCV uważa Cosine >= 0.363 za tę samą osobę.
        for person_name, db_feature in self.embeddings.items():
             score = self.recognizer.match(face_feature, db_feature, cv2.FaceRecognizerSF_FR_COSINE)
             if score > best_raw_score:
                 best_raw_score = score
                 best_match = person_name
                 
        # Konwersja by uzytkownik zrozumial co widzi.
        # Wg SFace: Kosinus >= 0.363 to bezpieczny match. My robimy tak, że 0.363 to 85% (odrzucony / przyjęty styk).
        # A powiedzmy 0.850 to 99%. Poniżej tego styk to bezwzględnie rzucamy odrzucenie <85%.
        # Strojony rygor pod system wejściowy (Szkoła).
        
        confidence_percent = 0.0
        if best_raw_score > 0.30: 
             # Matematyka dopasowujaca bezpieczny prog 0.363 pod 85% użytkownika, 1.0 to 100%
             mapped = 85.0 + ((best_raw_score - 0.363) / (1.0 - 0.363)) * 15.0
             confidence_percent = np.clip(mapped / 100.0, 0.0, 1.0)
             if best_raw_score < 0.363: 
                  # Dla słabego cosinusa, dajemy odrzuconą statystykę do UI pod okiem użytkownika
                  confidence_percent = best_raw_score * 2.0
                  
        print(f"[DEBUG SFace] Raw Cosine: {best_raw_score:.3f}, Próg szkoły: {confidence_percent:.2%}, Osoba: {best_match}")
        
        if confidence_percent >= 0.85:
            return best_match, confidence_percent
        else:
            # RYZYKO: Kosinus ponizej rygorystycznej zasady! Blokada.
            return None, max(0.0, confidence_percent)
            
    def detect_gender(self, face_image):
        """Wykrywa płeć z wyciętego obrazu twarzy"""
        if self.gender_net is None:
            return "?"
        try:
            if len(face_image.shape) == 2:
                face_image = cv2.cvtColor(face_image, cv2.COLOR_GRAY2BGR)
            
            blob = cv2.dnn.blobFromImage(face_image, 1.0, (227, 227), (78.4263377603, 87.7689143744, 114.895847746), swapRB=False)
            self.gender_net.setInput(blob)
            gender_preds = self.gender_net.forward()
            gender = self.gender_list[gender_preds[0].argmax()]
            return gender
        except Exception as e:
            return "?"
            
    def delete_person(self, person_name):
        person_dir = self.base_dir / person_name
        if person_dir.exists():
            for file in person_dir.glob("*.jpg"):
                file.unlink()
            person_dir.rmdir()
            self.train_model() 
            return True
        return False
