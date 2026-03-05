import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import cv2
from PIL import Image, ImageTk
from pathlib import Path
import numpy as np

from access_database import AccessDatabase
from face_recognition import FaceRecognition


class AccessControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🚪 System Kontroli Dostępu - Rozpoznawanie Twarzy")
        self.root.geometry("1200x700")
        self.root.configure(bg='#f0f0f0')
        
        # Inicjalizuj komponenty
        self.db = AccessDatabase()
        self.face_recognition = FaceRecognition()
        
        # Zmienne
        self.camera = None
        self.camera_active = False
        self.current_frame = None
        self.recognition_mode = "register"  # register lub recognize
        self.current_user_name = ""
        
        # Utwórz folder na zdjęcia
        self.output_dir = Path("face_database")
        self.output_dir.mkdir(exist_ok=True)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Utwórz interfejs"""
        # Górny panel
        top_frame = tk.Frame(self.root, bg='#1a1a1a', height=70)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        title_label = tk.Label(top_frame, text="🚪 SYSTEM KONTROLI DOSTĘPU",
                              font=("Arial", 20, "bold"), bg='#1a1a1a', fg='#00ff00')
        title_label.pack(pady=15)
        
        # Panel przycisków
        btn_frame = tk.Frame(self.root, bg='#f0f0f0')
        btn_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        # Przyciski główne
        tk.Button(btn_frame, text="➕ Zarejestruj Osobę",
                 command=self.register_mode, bg='#4CAF50', fg='white',
                 font=("Arial", 11, "bold"), width=20, height=2).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="🔍 Rozpoznawaj Twarz",
                 command=self.recognize_mode, bg='#2196F3', fg='white',
                 font=("Arial", 11, "bold"), width=20, height=2).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="📋 Zarządzaj Użytkownikami",
                 command=self.manage_users, bg='#FF9800', fg='white',
                 font=("Arial", 11, "bold"), width=20, height=2).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="📊 Historia Dostępu",
                 command=self.show_history, bg='#9C27B0', fg='white',
                 font=("Arial", 11, "bold"), width=20, height=2).pack(side=tk.LEFT, padx=5)
        
        # Ramka główna
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Lewa strona - obraz z kamery
        left_frame = tk.Frame(main_frame, bg='white', relief=tk.SUNKEN, bd=2)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.image_label = tk.Label(left_frame, text="Brak kamery", bg='white',
                                   font=("Arial", 14), fg='#888888')
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Prawa strona - informacje
        right_frame = tk.Frame(main_frame, bg='white', relief=tk.SUNKEN, bd=2, width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        # Tytuł
        self.info_title = tk.Label(right_frame, text="Status", bg='white',
                                  font=("Arial", 13, "bold"), fg='#333')
        self.info_title.pack(fill=tk.X, padx=5, pady=5)
        
        # Tekst informacyjny
        self.info_text = tk.Text(right_frame, height=18, width=40,
                                font=("Courier", 10), bg='#f9f9f9')
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.info_text.config(state=tk.DISABLED)
        
        # Status bar
        self.status_label = tk.Label(self.root, text="Gotowy",
                                    font=("Arial", 10), bg='#f0f0f0', fg='#333')
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        # Bind klawisza S
        self.root.bind('s', self.on_snapshot)
        self.root.bind('S', self.on_snapshot)
        
        self.update_info()
    
    def update_info(self):
        """Aktualizuj informacje"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        
        users = self.db.get_all_users()
        
        info = "=" * 35 + "\n"
        info += "ZAREJESTROWANE OSOBY\n"
        info += "=" * 35 + "\n\n"
        
        if users:
            for user_id, name, reg_date, status in users:
                status_icon = "✓" if status == "active" else "✗"
                info += f"{status_icon} {name}\n"
                info += f"   Zarejestrowana: {reg_date[:10]}\n\n"
        else:
            info += "Brak zarejestrowanych osób\n\n"
        
        info += "=" * 35 + "\n"
        info += f"RAZEM: {len(users)} osób\n"
        
        self.info_text.insert(tk.END, info)
        self.info_text.config(state=tk.DISABLED)
    
    def register_mode(self):
        """Tryb rejestracji"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Zarejestruj Nową Osobę")
        dialog.geometry("400x200")
        dialog.configure(bg='white')
        
        tk.Label(dialog, text="Wpisz imię i nazwisko:", bg='white',
                font=("Arial", 12)).pack(pady=10)
        
        name_entry = tk.Entry(dialog, font=("Arial", 12), width=30)
        name_entry.pack(pady=5)
        name_entry.focus()
        
        def start_registration():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Błąd", "Wpisz imię i nazwisko!")
                return
            
            dialog.destroy()
            self.do_register_face(name)
        
        tk.Button(dialog, text="Dalej", command=start_registration,
                 bg='#4CAF50', fg='white', font=("Arial", 11, "bold"),
                 width=20).pack(pady=10)
    
    def do_register_face(self, name):
        """Rejestruj twarz"""
        self.current_user_name = name
        self.recognition_mode = "register"
        
        # Włącz kamerę
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            messagebox.showerror("Błąd", "Nie można otworzyć kamery!")
            return
        
        self.camera_active = True
        self.status_label.config(text=f"Rejestrowanie: {name} - Naciśnij SPACJĘ aby sformatować twarz, S aby zapisać")
        self.register_loop()
    
    def recognize_mode(self):
        """Tryb rozpoznawania"""
        self.recognition_mode = "recognize"
        
        # Włącz kamerę
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            messagebox.showerror("Błąd", "Nie można otworzyć kamery!")
            return
        
        self.camera_active = True
        self.status_label.config(text="🔍 Rozpoznawanie - staniesz przed kamerą, system CI sprawdzą")
        self.recognize_loop()
    
    def register_loop(self):
        """Pętla rejestracji"""
        if not self.camera_active or not self.camera:
            return
        
        ret, frame = self.camera.read()
        if not ret:
            self.camera_active = False
            messagebox.showerror("Błąd", "Nie można czytać z kamery!")
            return
        
        frame = cv2.resize(frame, (640, 480))
        
        try:
            faces, gray = self.face_recognition.detect_faces(frame)
            
            if len(faces) > 0:
                # Narysuj prostokąt wokół pierwszej znalezionej twarzy
                x, y, w, h = faces[0]
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                cv2.putText(frame, "STOJ NIERUCHOMO!", (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                self.current_frame = frame
                self.current_face = gray[y:y+h, x:x+w]
                self.current_face_coords = (x, y, w, h)
            else:
                cv2.putText(frame, "Nie widze twarzy!", (50, 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            self.current_frame = frame
            self.display_image(frame)
            
        except Exception as e:
            print(f"Błąd: {e}")
        
        self.root.after(30, self.register_loop)
    
    def recognize_loop(self):
        """Pętla rozpoznawania"""
        if not self.camera_active or not self.camera:
            return
        
        ret, frame = self.camera.read()
        if not ret:
            self.camera_active = False
            return
        
        frame = cv2.resize(frame, (640, 480))
        
        try:
            faces, gray = self.face_recognition.detect_faces(frame)
            
            if len(faces) > 0:
                x, y, w, h = faces[0]
                face_gray = gray[y:y+h, x:x+w]
                face_gray = cv2.resize(face_gray, (200, 200))
                
                # Pobierz embedding
                embedding = self.face_recognition.get_face_embedding(face_gray)
                
                # Porównaj z wszystkimi użytkownikami
                users = self.db.get_all_users()
                best_match = None
                best_confidence = 0
                
                print(f"\n[ROZPOZNAWANIE] Embedding shape: {embedding.shape}")
                
                for user_id, name, reg_date, status in users:
                    stored_data = self.db.get_face_encoding(name)
                    if stored_data:
                        stored_array = np.frombuffer(stored_data, dtype=np.float32)
                        
                        print(f"[DEBUG] Porównuję z {name}: stored shape={stored_array.shape}")
                        
                        # Porównaj - NIŻSZY THRESHOLD DLA LEPSZEGO ROZPOZNANIA
                        match, confidence = self.face_recognition.compare_faces(
                            embedding.astype(np.float32), 
                            stored_array,
                            threshold=0.55
                        )
                        
                        print(f"[DEBUG] {name}: match={match}, confidence={confidence:.2%}")
                        
                        if confidence > best_confidence:
                            best_confidence = confidence
                            if match:
                                best_match = name
                
                # Narysuj wynik
                if best_match:
                    color = (0, 255, 0)  # Zielony
                    label = f"✓ {best_match} ({best_confidence:.0%})"
                    
                    # Zaloguj dostęp
                    self.db.log_access(best_match, "ACCEPTED", best_confidence)
                    
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)
                    cv2.putText(frame, "DOSTĘP PRZYZNANY!", (50, 50),
                               cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                else:
                    color = (0, 0, 255)  # Czerwony
                    label = f"NIEZNANA OSOBA ({best_confidence:.0%})"
                    
                    # Zaloguj odmowę
                    self.db.log_access("unknown", "DENIED", best_confidence)
                    
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)
                    cv2.putText(frame, "DOSTĘP ODMÓWIONY!", (50, 50),
                               cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
                
                cv2.putText(frame, label, (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            self.current_frame = frame
            self.display_image(frame)
            
        except Exception as e:
            print(f"Błąd rozpoznawania: {e}")
        
        self.root.after(30, self.recognize_loop)
    
    def display_image(self, cv_image):
        """Wyświetl obraz"""
        try:
            if cv_image is None:
                return
            
            cv_rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            cv_rgb = cv2.resize(cv_rgb, (550, 410))
            
            pil_image = Image.fromarray(cv_rgb)
            photo = ImageTk.PhotoImage(pil_image)
            
            self.image_label.config(image=photo)
            self.image_label.image = photo
            
        except Exception as e:
            print(f"Błąd wyświetlania: {e}")
    
    def on_snapshot(self, event=None):
        """Klawisz S - zapisz twarz"""
        if not self.camera_active or self.current_frame is None:
            return
        
        if self.recognition_mode == "register":
            self.save_registered_face()
        else:
            messagebox.showinfo("Info", "Tryb rozpoznawania. Wciśnij Stop aby zamknąć.")
    
    def save_registered_face(self):
        """Zapisz zarejestrowaną twarz"""
        if not hasattr(self, 'current_face'):
            messagebox.showwarning("Błąd", "Twarz nie znaleziona!")
            return
        
        try:
            # Pobierz embedding (current_face jest już grayscale)
            embedding = self.face_recognition.get_face_embedding(self.current_face)
            
            print(f"[REJESTRACJA] Embedding shape: {embedding.shape}")
            
            # Zapisz w bazie
            self.db.register_face(self.current_user_name, embedding)
            
            # Zapisz zdjęcie
            output_path = self.output_dir / f"{self.current_user_name}.jpg"
            cv2.imwrite(str(output_path), self.current_face)
            
            # Zamknij kamerę
            self.camera_active = False
            if self.camera:
                self.camera.release()
                self.camera = None
            
            messagebox.showinfo("Sukces!", f"✓ Osoba '{self.current_user_name}' zarejestrowana!")
            self.status_label.config(text="Gotowy")
            self.update_info()
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd rejestracji: {str(e)}")
            print(f"[BŁĄD REJESTRACJI] {e}")
    
    def manage_users(self):
        """Zarządzaj użytkownikami"""
        users = self.db.get_all_users()
        
        if not users:
            messagebox.showinfo("Brak danych", "Brak zarejestrowanych osób!")
            return
        
        window = tk.Toplevel(self.root)
        window.title("Zarządzaj Użytkownikami")
        window.geometry("500x400")
        window.configure(bg='white')
        
        # Tabela
        columns = ("ID", "Imię", "Data Rejestracji", "Status")
        tree = ttk.Treeview(window, columns=columns, height=12)
        tree.column("#0", width=0, stretch=tk.NO)
        tree.column("ID", anchor=tk.CENTER, width=40)
        tree.column("Imię", anchor=tk.W, width=150)
        tree.column("Data Rejestracji", anchor=tk.CENTER, width=120)
        tree.column("Status", anchor=tk.CENTER, width=80)
        
        tree.heading("#0", text="", anchor=tk.W)
        tree.heading("ID", text="ID", anchor=tk.CENTER)
        tree.heading("Imię", text="Imię", anchor=tk.W)
        tree.heading("Data Rejestracji", text="Data", anchor=tk.CENTER)
        tree.heading("Status", text="Status", anchor=tk.CENTER)
        
        for user_id, name, reg_date, status in users:
            tree.insert("", tk.END, values=(user_id, name, reg_date[:10], status))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        def delete_user():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Błąd", "Wybierz osobę!")
                return
            
            item = tree.item(selected[0])
            user_id = item['values'][1]
            
            # Znajdź imię
            for uid, name, _, _ in users:
                if uid == user_id:
                    self.db.delete_user(name)
                    messagebox.showinfo("Sukces", f"Usunięto: {name}")
                    window.destroy()
                    self.update_info()
                    break
        
        tk.Button(window, text="Usuń Wybraną Osobę", command=delete_user,
                 bg='#f44336', fg='white', font=("Arial", 11, "bold"),
                 width=30).pack(pady=10)
    
    def show_history(self):
        """Pokaż historię dostępu"""
        history = self.db.get_access_history(30)
        
        if not history:
            messagebox.showinfo("Historia", "Brak zapis w historii!")
            return
        
        window = tk.Toplevel(self.root)
        window.title("Historia Dostępu")
        window.geometry("600x400")
        window.configure(bg='white')
        
        columns = ("Osoba", "Czas Dostępu", "Typ", "Pewność")
        tree = ttk.Treeview(window, columns=columns, height=15)
        tree.column("#0", width=0, stretch=tk.NO)
        tree.column("Osoba", anchor=tk.W, width=150)
        tree.column("Czas Dostępu", anchor=tk.CENTER, width=150)
        tree.column("Typ", anchor=tk.CENTER, width=100)
        tree.column("Pewność", anchor=tk.CENTER, width=100)
        
        tree.heading("#0", text="", anchor=tk.W)
        tree.heading("Osoba", text="Osoba", anchor=tk.W)
        tree.heading("Czas Dostępu", text="Czas", anchor=tk.CENTER)
        tree.heading("Typ", text="Typ", anchor=tk.CENTER)
        tree.heading("Pewność", text="Pewność", anchor=tk.CENTER)
        
        for user_name, access_time, access_type, confidence in history:
            status = "✓ PRZYJĘTY" if access_type == "ACCEPTED" else "✗ ODMÓWIONO"
            conf_str = f"{confidence*100:.0f}%" if confidence else "N/A"
            tree.insert("", tk.END, values=(user_name or "Nieznana", access_time[5:16], status, conf_str))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = AccessControlApp(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        if app.camera:
            app.camera.release()
        root.destroy()
