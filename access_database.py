import sqlite3
import os
from datetime import datetime
from pathlib import Path
import json

class AccessDatabase:
    def __init__(self, db_path='access_system.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicjalizuj bazę danych"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela zarejestrowanych osób
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                face_data BLOB NOT NULL,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # Tabela historii dostępu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT,
                access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_type TEXT,
                confidence REAL,
                FOREIGN KEY (user_name) REFERENCES users(name)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def register_face(self, name, face_encoding):
        """Zarejestruj nową twarz"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Konwertuj encoding na bytes
            face_data = face_encoding.tobytes()
            
            cursor.execute('''
                INSERT OR REPLACE INTO users (name, face_data)
                VALUES (?, ?)
            ''', (name, face_data))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Błąd rejestracji: {e}")
            return False
    
    def get_all_users(self):
        """Pobierz listę wszystkich zarejestrowanych użytkowników"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, name, registration_date, status FROM users')
        rows = cursor.fetchall()
        conn.close()
        
        return rows
    
    def get_face_encoding(self, name):
        """Pobierz encoding twarzy dla danej osoby"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT face_data FROM users WHERE name = ? AND status = "active"', (name,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return row[0]
        return None
    
    def log_access(self, user_name, access_type, confidence):
        """Zaloguj dostęp do systemu"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO access_log (user_name, access_type, confidence)
            VALUES (?, ?, ?)
        ''', (user_name, access_type, confidence))
        
        conn.commit()
        conn.close()
    
    def get_access_history(self, limit=50):
        """Pobierz historię dostępu"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_name, access_time, access_type, confidence 
            FROM access_log 
            ORDER BY access_time DESC 
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        return rows
    
    def delete_user(self, name):
        """Usuń użytkownika"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM users WHERE name = ?', (name,))
        conn.commit()
        conn.close()
