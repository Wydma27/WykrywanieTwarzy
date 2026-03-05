import cv2
import os
from pathlib import Path

class FaceDetector:
    def __init__(self):
        """Inicjalizuj detektor twarzy"""
        # Załaduj cascadę do detekcji twarzy
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if self.face_cascade.empty():
            raise Exception("Nie można załadować kaskady twarzy!")
    
    def detect_faces_in_image(self, image_path):
        """Wykryj twarze na zdjęciu"""
        image = cv2.imread(str(image_path))
        
        if image is None:
            raise Exception(f"Nie można otworzyć zdjęcia: {image_path}")
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        return image, faces, gray
    
    def detect_faces_from_camera(self, frame):
        """Wykryj twarze w klatce z kamery"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        return frame, faces, gray
    
    def draw_faces(self, image, faces):
        """Narysuj prostokąty wokół twarzy"""
        image_with_faces = image.copy()
        
        for (x, y, w, h) in faces:
            cv2.rectangle(image_with_faces, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(image_with_faces, 'Twarz', (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return image_with_faces
    
    def save_detected_image(self, image, output_path):
        """Zapisz zdjęcie z zaznaczonymi twarzami"""
        cv2.imwrite(str(output_path), image)
        return output_path
    
    def get_face_coordinates(self, faces):
        """Uzyskaj współrzędne twarzy"""
        coordinates = []
        for idx, (x, y, w, h) in enumerate(faces):
            coordinates.append({
                'face_id': idx + 1,
                'x': int(x),
                'y': int(y),
                'width': int(w),
                'height': int(h)
            })
        return coordinates
