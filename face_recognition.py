import cv2
import numpy as np
from pathlib import Path

class FaceRecognition:
    def __init__(self):
        """Inicjalizuj system rozpoznawania twarzy"""
        # Załaduj cascadę do detekcji
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Inicjalizuj LBP (Local Binary Patterns) dla rozpoznawania
        self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
        
        if self.face_cascade.empty():
            raise Exception("Nie można załadować kaskady twarzy!")
    
    def detect_faces(self, image):
        """Wykryj twarze na obrazie"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(100, 100)  # Większy minimum dla lepszej jakości
        )
        return faces, gray
    
    def extract_face(self, image, face_coords):
        """Wyciągnij obszar twarzy z obrazu"""
        x, y, w, h = face_coords
        face_roi = image[y:y+h, x:x+w]
        
        # Zmień rozmiar do standardowego (200x200)
        face_roi = cv2.resize(face_roi, (200, 200))
        
        return face_roi
    
    def get_face_embedding(self, face_image):
        """Uzyskaj wektor cech (embedding) twarzy - lepszy algorytm"""
        # Upewnij się że to grayscale
        if len(face_image.shape) == 3:
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = face_image
        
        # Resize do standardowego rozmiaru
        gray = cv2.resize(gray, (100, 100))
        
        # Histogram po całym obrazie
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = cv2.normalize(hist, hist).flatten()
        
        # Dodaj więcej cech - podziel na regiony
        h, w = gray.shape
        regions = []
        for i in range(2):
            for j in range(2):
                region = gray[i*h//2:(i+1)*h//2, j*w//2:(j+1)*w//2]
                hist_region = cv2.calcHist([region], [0], None, [64], [0, 256])
                hist_region = cv2.normalize(hist_region, hist_region).flatten()
                regions.extend(hist_region)
        
        # Zmerguj wszystkie cechy
        embedding = np.concatenate([hist, regions])
        
        return embedding.astype(np.float32)
    
    def compare_faces(self, encoding1, encoding2, threshold=0.5):
        """Porównaj dwa embeddingi twarzy - lepszy algorytm"""
        if encoding1 is None or encoding2 is None:
            print("Błąd: Brak embeddingu!")
            return False, 0.0
        
        # Upewnij się że są tego samego rozmiaru
        if len(encoding1) != len(encoding2):
            print(f"Błąd: Różne rozmiary {len(encoding1)} vs {len(encoding2)}")
            return False, 0.0
        
        # Kosinus podobieństwo (lepsza odległość dla histogramów)
        dot_product = np.dot(encoding1, encoding2)
        norm1 = np.linalg.norm(encoding1)
        norm2 = np.linalg.norm(encoding2)
        
        if norm1 == 0 or norm2 == 0:
            return False, 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Normalizuj do 0-1
        similarity = (similarity + 1) / 2
        
        print(f"[DEBUG] Porównanie: {similarity:.2%} (próg: {threshold:.0%})")
        
        return similarity > threshold, similarity
    
    def draw_face_box(self, image, faces, labels=None, colors=None):
        """Narysuj prostokąty wokół twarzy"""
        image_copy = image.copy()
        
        for idx, (x, y, w, h) in enumerate(faces):
            color = colors[idx] if colors else (0, 255, 0)
            cv2.rectangle(image_copy, (x, y), (x + w, y + h), color, 3)
            
            if labels and idx < len(labels):
                label = labels[idx]
                cv2.putText(image_copy, label, (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        
        return image_copy
