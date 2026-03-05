import sqlite3
import os
from datetime import datetime
from pathlib import Path

class Database:
    def __init__(self, db_path='face_detection.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicjalizuj bazę danych"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela do przechowywania informacji o twarzach
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS faces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_name TEXT NOT NULL,
                image_path TEXT NOT NULL,
                num_faces INTEGER NOT NULL,
                detection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                face_coordinates TEXT
            )
        ''')
        
        # Tabela do statystyk
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_images_analyzed INTEGER DEFAULT 0,
                total_faces_detected INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_detection(self, image_name, image_path, num_faces, face_coords):
        """Dodaj nowe wykrycie do bazy"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO faces (image_name, image_path, num_faces, face_coordinates)
            VALUES (?, ?, ?, ?)
        ''', (image_name, image_path, num_faces, str(face_coords)))
        
        conn.commit()
        conn.close()
    
    def get_all_detections(self):
        """Pobierz wszystkie wykrycia"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM faces ORDER BY detection_date DESC')
        rows = cursor.fetchall()
        conn.close()
        
        return rows
    
    def get_statistics(self):
        """Pobierz statystyki"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as images, SUM(num_faces) as faces FROM faces')
        result = cursor.fetchone()
        conn.close()
        
        return {
            'total_images': result[0] if result[0] else 0,
            'total_faces': result[1] if result[1] else 0
        }
    
    def delete_detection(self, detection_id):
        """Usuń wykrycie z bazy"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM faces WHERE id = ?', (detection_id,))
        
        conn.commit()
        conn.close()
