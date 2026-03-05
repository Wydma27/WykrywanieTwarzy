import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
from PIL import Image, ImageTk
import threading
from pathlib import Path
import os

from database import Database
from face_detector import FaceDetector


class FaceDetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplikacja do Detekcji Twarzy")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # Inicjalizuj bazę danych i detektor
        self.db = Database()
        self.detector = FaceDetector()
        
        # Zmienne
        self.camera = None
        self.camera_active = False
        self.current_frame = None
        self.camera_capture_counter = 0
        
        # Utwórz katalog na zdjęcia
        self.output_dir = Path("detected_faces")
        self.output_dir.mkdir(exist_ok=True)
        
        # Interfejs
        self.setup_ui()
    
    def setup_ui(self):
        """Utwórz interfejs użytkownika"""
        # Górny panel
        top_frame = tk.Frame(self.root, bg='#333333', height=60)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        title_label = tk.Label(top_frame, text="🔍 Detektor Twarzy OpenCV",
                              font=("Arial", 18, "bold"), bg='#333333', fg='white')
        title_label.pack(pady=10)
        
        # Panel przycisków
        button_frame = tk.Frame(self.root, bg='#f0f0f0')
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        # Przyciski główne
        btn_load_image = tk.Button(button_frame, text="📁 Wczytaj Zdjęcie",
                                   command=self.load_image, bg='#4CAF50', fg='white',
                                   font=("Arial", 10, "bold"), width=18)
        btn_load_image.pack(side=tk.LEFT, padx=5)
        
        btn_camera = tk.Button(button_frame, text="📷 Włącz Kamerę",
                               command=self.toggle_camera, bg='#2196F3', fg='white',
                               font=("Arial", 10, "bold"), width=18)
        btn_camera.pack(side=tk.LEFT, padx=5)
        
        btn_history = tk.Button(button_frame, text="📊 Historia",
                                command=self.show_history, bg='#FF9800', fg='white',
                                font=("Arial", 10, "bold"), width=18)
        btn_history.pack(side=tk.LEFT, padx=5)
        
        btn_stats = tk.Button(button_frame, text="📈 Statystyki",
                              command=self.show_statistics, bg='#9C27B0', fg='white',
                              font=("Arial", 10, "bold"), width=18)
        btn_stats.pack(side=tk.LEFT, padx=5)
        
        # Ramka główna
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Lewa strona - obraz
        left_frame = tk.Frame(main_frame, bg='white', relief=tk.SUNKEN, bd=2)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        img_label = tk.Label(left_frame, text="Brak zdjęcia", bg='white',
                            font=("Arial", 12), fg='#888888')
        img_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.image_label = img_label
        
        # Prawa strona - informacje
        right_frame = tk.Frame(main_frame, bg='white', relief=tk.SUNKEN, bd=2, width=250)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(5, 0))
        right_frame.pack_propagate(False)  # Zatrzymaj rozmiar na 250px
        
        # Wyniki
        results_title = tk.Label(right_frame, text="Wyniki", bg='white',
                                font=("Arial", 12, "bold"))
        results_title.pack(fill=tk.X, padx=5, pady=5)
        
        self.results_text = tk.Text(right_frame, height=12, width=30, 
                                    font=("Courier", 10), bg='#f9f9f9')
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Dolny panel - statystyki
        footer_frame = tk.Frame(self.root, bg='#f0f0f0')
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        self.status_label = tk.Label(footer_frame, text="Gotowy",
                                     font=("Arial", 10), bg='#f0f0f0', fg='#666666')
        self.status_label.pack(side=tk.LEFT)
        
        self.stats_label = tk.Label(footer_frame, text="",
                                    font=("Arial", 10), bg='#f0f0f0', fg='#666666')
        self.stats_label.pack(side=tk.RIGHT)
        
        # Bind klawisza 'S' do robienia zdjęć
        self.root.bind('s', self.on_camera_snapshot)
        self.root.bind('S', self.on_camera_snapshot)
        
        self.update_stats()
    
    def on_camera_snapshot(self, event=None):
        """Klawisz 'S' - jak kamera jest aktywna, zrób zdjęcie"""
        if not self.camera_active or self.current_frame is None:
            return
        
        try:
            self.camera_capture_counter += 1
            output_path = self.output_dir / f"capture_{self.camera_capture_counter}.jpg"
            
            # Zapisz zdjęcie
            cv2.imwrite(str(output_path), self.current_frame)
            
            # Wykryj twarze na zdjęciu
            frame_with_faces, faces, gray = self.detector.detect_faces_from_camera(self.current_frame)
            coords = self.detector.get_face_coordinates(faces)
            
            # Dodaj do bazy
            self.db.add_detection(
                f"capture_{self.camera_capture_counter}.jpg",
                str(output_path),
                len(faces),
                coords
            )
            
            messagebox.showinfo("✓ Sukces", f"Zdjęcie nr {self.camera_capture_counter} zapisane!\n\nZnalezione twarze: {len(faces)}")
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zapisać zdjęcia: {str(e)}")
    
    def load_image(self):
        """Wczytaj zdjęcie z dysku"""
        file_path = filedialog.askopenfilename(
            title="Wybierz zdjęcie",
            filetypes=[("Obrazy", "*.jpg *.jpeg *.png *.bmp"),
                      ("Wszystkie pliki", "*.*")]
        )
        
        if not file_path:
            return
        
        self.status_label.config(text="Przetwarzanie zdjęcia...")
        self.root.update()
        
        try:
            image, faces, gray = self.detector.detect_faces_in_image(file_path)
            image_with_faces = self.detector.draw_faces(image, faces)
            
            # Zapisz wynik
            output_path = self.output_dir / f"detected_{Path(file_path).stem}.jpg"
            self.detector.save_detected_image(image_with_faces, output_path)
            
            # Dodaj do bazy danych
            coords = self.detector.get_face_coordinates(faces)
            self.db.add_detection(
                Path(file_path).name,
                str(file_path),
                len(faces),
                coords
            )
            
            # Wyświetl obraz
            self.display_image(image_with_faces)
            
            # Pokaż wyniki
            self.show_results(len(faces), coords, file_path)
            
            self.status_label.config(text=f"✓ Znaleziono {len(faces)} twarzy!")
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd podczas przetwarzania: {str(e)}")
            self.status_label.config(text="Błąd!")
    
    def toggle_camera(self):
        """Włącz/wyłącz kamerę"""
        if not self.camera_active:
            try:
                self.camera = cv2.VideoCapture(0)
                
                # Sprawdź czy udało się otworzyć kamerę
                if not self.camera.isOpened():
                    messagebox.showerror("Błąd Kamery", "Nie można otworzyć kamery!\n\nSprawdź czy:\n✓ Kamera jest podłączona\n✓ Sterowniki są zainstalowane\n✓ Żadna inna app. nie używa kamery")
                    self.status_label.config(text="Gotowy")
                    self.camera = None
                    return
                
                # Ustaw parametry kamery
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.camera.set(cv2.CAP_PROP_FPS, 30)
                
                self.camera_active = True
                self.camera_capture_counter = 0
                self.status_label.config(text="🔴 Kamera WŁĄCZONA (S=zdjęcie, kliknij ponownie=wyłącz)")
                self.camera_loop()
                
            except Exception as e:
                messagebox.showerror("Błąd", f"Błąd kamery:\n{str(e)}")
                self.status_label.config(text="Gotowy")
                self.camera = None
        else:
            # Wyłącz kamerę
            self.camera_active = False
            if self.camera:
                self.camera.release()
                self.camera = None
            self.status_label.config(text="Gotowy")
            self.image_label.config(image='')
            self.image_label.config(text="Kamera wyłączona", fg='#888888')
            self.results_text.config(state=tk.NORMAL)
            self.results_text.delete(1.0, tk.END)
            self.results_text.config(state=tk.DISABLED)
    
    def camera_loop(self):
        """Pętla kamery - uruchom w Tkinter"""
        if not self.camera_active or not self.camera:
            return
        
        try:
            ret, frame = self.camera.read()
            
            if not ret:
                self.camera_active = False
                messagebox.showerror("Błąd", "Nie można czytać z kamery!")
                self.status_label.config(text="Gotowy")
                self.camera.release()
                self.camera = None
                return
            
            # Prosta obróbka bez zmniejszania sie - pełne rozdzielczość
            frame = cv2.resize(frame, (640, 480))
            
            # Wykryj twarze
            try:
                frame_with_faces, faces, gray = self.detector.detect_faces_from_camera(frame)
            except Exception as e:
                print(f"Błąd detekcji: {e}")
                faces = []
                frame_with_faces = frame
            
            # Wyświetl
            self.current_frame = frame_with_faces.copy()
            self.display_image(frame_with_faces)
            
            # Pokaż wyniki
            if len(faces) > 0:
                coords = self.detector.get_face_coordinates(faces)
                self.show_results(len(faces), coords, "🎥 Kamera Live")
            else:
                self.results_text.config(state=tk.NORMAL)
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, "Brak twarzy\n\nNaciśnij 'S'\naby zapisać\nzdjęcie")
                self.results_text.config(state=tk.DISABLED)
            
            # Zaplanuj następną klatkę (33ms = ~30 FPS)
            self.root.after(33, self.camera_loop)
            
        except Exception as e:
            print(f"Błąd pętli kamery: {e}")
            self.camera_active = False
            self.status_label.config(text="Gotowy")
            if self.camera:
                self.camera.release()
                self.camera = None
    
    def display_image(self, cv_image):
        """Wyświetl obraz w GUI - odporna na błędy"""
        try:
            if cv_image is None:
                return
            
            # Upewnij się że obraz jest numpy array
            if not isinstance(cv_image, type(cv_image)):
                return
            
            # Konwertuj BGR na RGB
            if len(cv_image.shape) == 3:
                cv_rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            else:
                cv_rgb = cv2.cvtColor(cv_image, cv2.COLOR_GRAY2RGB)
            
            # Zmień rozmiar do okna
            h, w = cv_rgb.shape[:2]
            if h > 0 and w > 0:
                aspect_ratio = w / h
                new_w = 450
                new_h = int(new_w / aspect_ratio)
                
                if new_h > 0 and new_w > 0:
                    cv_rgb = cv2.resize(cv_rgb, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            
            # Konwertuj do PIL
            pil_image = Image.fromarray(cv_rgb)
            photo = ImageTk.PhotoImage(pil_image)
            
            # Wyświetl
            self.image_label.config(image=photo)
            self.image_label.image = photo
            
        except Exception as e:
            print(f"[Display Error] {str(e)}")
    
    def show_results(self, num_faces, coords, source):
        """Pokaż wyniki detekcji"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        
        result_text = f"Źródło: {Path(source).name if isinstance(source, str) else source}\n"
        result_text += f"{'='*28}\n\n"
        result_text += f"Znalezione twarze: {num_faces}\n\n"
        
        if num_faces > 0:
            result_text += "Współrzędne:\n"
            for coord in coords:
                result_text += f"\nTwarz #{coord['face_id']}:\n"
                result_text += f"  X: {coord['x']}\n"
                result_text += f"  Y: {coord['y']}\n"
                result_text += f"  W: {coord['width']}\n"
                result_text += f"  H: {coord['height']}\n"
        
        self.results_text.insert(tk.END, result_text)
        self.results_text.config(state=tk.DISABLED)
    
    def show_history(self):
        """Pokaż historię detekcji"""
        detections = self.db.get_all_detections()
        
        if not detections:
            messagebox.showinfo("Historia", "Brak danych w historii!")
            return
        
        history_window = tk.Toplevel(self.root)
        history_window.title("Historia Detekcji")
        history_window.geometry("600x400")
        
        # Tabela
        columns = ("ID", "Zdjęcie", "Twarze", "Data")
        tree = ttk.Treeview(history_window, columns=columns, height=15)
        tree.column("#0", width=0, stretch=tk.NO)
        tree.column("ID", anchor=tk.CENTER, width=40)
        tree.column("Zdjęcie", anchor=tk.W, width=250)
        tree.column("Twarze", anchor=tk.CENTER, width=60)
        tree.column("Data", anchor=tk.CENTER, width=150)
        
        tree.heading("#0", text="", anchor=tk.W)
        tree.heading("ID", text="ID", anchor=tk.CENTER)
        tree.heading("Zdjęcie", text="Zdjęcie", anchor=tk.W)
        tree.heading("Twarze", text="Twarze", anchor=tk.CENTER)
        tree.heading("Data", text="Data", anchor=tk.CENTER)
        
        for detection in detections:
            tree.insert("", tk.END, values=(
                detection[0],
                detection[1],
                detection[3],
                detection[5]
            ))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Przycisk usunięcia
        def delete_selected():
            selected = tree.selection()
            if selected:
                item = tree.item(selected[0])
                detection_id = item['values'][0]
                self.db.delete_detection(detection_id)
                tree.delete(selected)
                messagebox.showinfo("Sukces", "Wykrycie usunięte!")
        
        btn_delete = tk.Button(history_window, text="Usuń zaznaczone",
                              command=delete_selected, bg='#f44336', fg='white')
        btn_delete.pack(side=tk.BOTTOM, padx=5, pady=5)
    
    def show_statistics(self):
        """Pokaż statystyki"""
        stats = self.db.get_statistics()
        
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Statystyki")
        stats_window.geometry("400x250")
        stats_window.configure(bg='white')
        
        title = tk.Label(stats_window, text="📊 Statystyki Detekcji",
                        font=("Arial", 16, "bold"), bg='white')
        title.pack(pady=20)
        
        stats_frame = tk.Frame(stats_window, bg='white')
        stats_frame.pack(pady=20)
        
        # Statystyka 1
        stat1_frame = tk.Frame(stats_frame, bg='#e3f2fd', relief=tk.RAISED, bd=2)
        stat1_frame.pack(fill=tk.X, padx=20, pady=10)
        
        label1 = tk.Label(stat1_frame, text="Przeanalizowano zdjęć:",
                         font=("Arial", 12), bg='#e3f2fd')
        label1.pack(side=tk.LEFT, padx=10, pady=10)
        
        value1 = tk.Label(stat1_frame, text=str(stats['total_images']),
                         font=("Arial", 14, "bold"), bg='#e3f2fd', fg='#1976d2')
        value1.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Statystyka 2
        stat2_frame = tk.Frame(stats_frame, bg='#f3e5f5', relief=tk.RAISED, bd=2)
        stat2_frame.pack(fill=tk.X, padx=20, pady=10)
        
        label2 = tk.Label(stat2_frame, text="Wykryto twarzy:",
                         font=("Arial", 12), bg='#f3e5f5')
        label2.pack(side=tk.LEFT, padx=10, pady=10)
        
        value2 = tk.Label(stat2_frame, text=str(stats['total_faces']),
                         font=("Arial", 14, "bold"), bg='#f3e5f5', fg='#7b1fa2')
        value2.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Średnia
        if stats['total_images'] > 0:
            avg = stats['total_faces'] / stats['total_images']
            stat3_frame = tk.Frame(stats_frame, bg='#e8f5e9', relief=tk.RAISED, bd=2)
            stat3_frame.pack(fill=tk.X, padx=20, pady=10)
            
            label3 = tk.Label(stat3_frame, text="Średnio twarzy/zdjęcie:",
                             font=("Arial", 12), bg='#e8f5e9')
            label3.pack(side=tk.LEFT, padx=10, pady=10)
            
            value3 = tk.Label(stat3_frame, text=f"{avg:.2f}",
                             font=("Arial", 14, "bold"), bg='#e8f5e9', fg='#388e3c')
            value3.pack(side=tk.RIGHT, padx=10, pady=10)
    
    def update_stats(self):
        """Aktualizuj statystyki w pasku dolnym"""
        stats = self.db.get_statistics()
        self.stats_label.config(
            text=f"Zdjęcia: {stats['total_images']} | Twarze: {stats['total_faces']}"
        )
        self.root.after(5000, self.update_stats)


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = FaceDetectionApp(root)
        root.mainloop()
    except Exception as e:
        import traceback
        print("=" * 60)
        print("❌ BŁĄD W APLIKACJI!")
        print("=" * 60)
        print(f"\nBłąd: {str(e)}")
        print("\nSzczegóły:")
        traceback.print_exc()
        print("\n" + "=" * 60)
        print("Naciśnij Enter aby zamknąć...")
        input()
        exit(1)
