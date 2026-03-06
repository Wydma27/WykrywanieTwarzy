import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
from pathlib import Path
import numpy as np
from datetime import datetime
import platform

# Ustawienia CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Import dźwięku
try:
    if platform.system() == "Windows":
        import winsound
except ImportError:
    pass

from face_base import FaceBase


class AccessControlSimple:
    def __init__(self, root):
        self.root = root
        self.root.title("🚪 Kontrola Dostępu - System Biometryczny SI")
        self.root.geometry("1200x750")
        
        # Inicjalizuj bazę (folder ze zdjęciami)
        self.face_base = FaceBase("face_database")
        
        # Zmienne
        self.camera = None
        self.camera_active = False
        self.current_frame = None
        self.access_log = []
        
        # Tracking wyników skanowania (Wsparcie dla wielu osób)
        self.last_scan_times = {} # {imię: timestamp}
        self.last_unknown_time = 0
        self.frame_count = 0
        self.detected_faces_results = [] # Lista słowników [{name, confidence, gender, box}]
        
        self.setup_ui()
        
        # Automatyczny start skanowania po uruchomieniu
        self.root.after(1000, self.start_scan)
    
    def setup_ui(self):
        """Utwórz interfejs (Nowoczesny)"""
        
        # Główny kontener grid
        self.root.grid_columnconfigure(0, weight=3)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        # 1. Górny pasek tytułowy
        self.top_frame = ctk.CTkFrame(self.root, fg_color="#1E1E2E", corner_radius=0, height=80)
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        self.title_label = ctk.CTkLabel(self.top_frame, text="🛡️ SYSTEM KONTROLI DOSTĘPU", 
                                        font=ctk.CTkFont(size=28, weight="bold"), text_color="#A6E3A1")
        self.title_label.place(relx=0.5, rely=0.5, anchor="center")

        # 2. Główny panel Lewy (Kamera i Przyciski)
        self.left_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.left_frame.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
        self.left_frame.grid_rowconfigure(1, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)

        # Pasek narzędzi
        self.toolbar = ctk.CTkFrame(self.left_frame, fg_color="#181825", corner_radius=10)
        self.toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        # Przyciski
        btn_font = ctk.CTkFont(size=14, weight="bold")
        
        self.btn_add = ctk.CTkButton(self.toolbar, text="➕ DODAJ OSOBĘ", font=btn_font, 
                                     fg_color="#A6E3A1", text_color="#11111B", hover_color="#94E2D5", 
                                     command=self.add_person, width=150, height=45)
        self.btn_add.pack(side="left", padx=10, pady=15)

        self.btn_scan = ctk.CTkButton(self.toolbar, text="🔍 SKANUJ TWARZ", font=btn_font,
                                      fg_color="#89B4FA", text_color="#11111B", hover_color="#74C7EC",
                                      command=self.start_scan, width=150, height=45)
        self.btn_scan.pack(side="left", padx=10, pady=15)
        
        self.btn_stop = ctk.CTkButton(self.toolbar, text="⏹️ STOP", font=btn_font,
                                      fg_color="#F38BA8", text_color="#11111B", hover_color="#F9E2AF", 
                                      command=self.stop_camera, width=120, height=45)
        self.btn_stop.pack(side="left", padx=10, pady=15)

        # Miejsce na kamerę
        self.camera_frame = ctk.CTkFrame(self.left_frame, fg_color="#11111B", corner_radius=15)
        self.camera_frame.grid(row=1, column=0, sticky="nsew")
        self.camera_frame.pack_propagate(False)

        self.camera_label = ctk.CTkLabel(self.camera_frame, text="KAMERA WYŁĄCZONA", 
                                         font=ctk.CTkFont(size=24, weight="bold"), text_color="#585B70")
        self.camera_label.place(relx=0.5, rely=0.5, anchor="center")

        # 3. Boczny panel (Dane, baza, historia)
        self.right_frame = ctk.CTkFrame(self.root, fg_color="#181825", width=350, corner_radius=15)
        self.right_frame.grid(row=1, column=1, padx=(0, 20), pady=20, sticky="nsew")
        self.right_frame.grid_propagate(False)

        self.info_title = ctk.CTkLabel(self.right_frame, text="STATUS SYSTEMU", 
                                       font=ctk.CTkFont(size=18, weight="bold"), text_color="#CDD6F4")
        self.info_title.pack(pady=(20, 10))

        # Przyciski boczne
        self.btn_list = ctk.CTkButton(self.right_frame, text="📋 LISTA OSÓB", font=btn_font,
                                      fg_color="#F9E2AF", text_color="#11111B", hover_color="#FAB387",
                                      command=self.show_people, height=40)
        self.btn_list.pack(fill="x", padx=20, pady=5)

        self.btn_history = ctk.CTkButton(self.right_frame, text="📊 HISTORIA LOGOWAŃ", font=btn_font,
                                         fg_color="#CBA6F7", text_color="#11111B", hover_color="#B4BEFE",
                                         command=self.show_history, height=40)
        self.btn_history.pack(fill="x", padx=20, pady=(5, 15))

        # Pole tekstowe do wyświetlania na żywo
        self.info_text = ctk.CTkTextbox(self.right_frame, fg_color="#1E1E2E", text_color="#A6E3A1", 
                                        font=ctk.CTkFont(family="Courier", size=13))
        self.info_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # 4. Dolny pasek (Status)
        self.status_bar = ctk.CTkLabel(self.root, text="System Gotowy", fg_color="#1E1E2E", 
                                       text_color="#A6ADC8", font=ctk.CTkFont(size=14), height=30)
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")

        self.update_info()
    
    def update_info(self):
        """Aktualizuj panel informacyjny"""
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", "end")
        
        people = self.face_base.get_all_people()
        
        text = "╔════════════════════════╗\n"
        text += "║ STACJA GŁÓWNA (MOD.AI) ║\n"
        text += "╚════════════════════════╝\n\n"
        
        if people:
            for i, person in enumerate(people, 1):
                images = self.face_base.get_person_images(person)
                text += f"[✓] {person} ({len(images)} foto)\n"
        else:
            text += "[!] Brak zapisanych osób.\n\n"
            text += "➔ Kliknij 'DODAJ OSOBĘ'\n"
            text += "➔ System wytrenuje z 1 foto.\n"
        
        text += f"\n{'─'*26}\n"
        text += f"RAZEM W BAZIE: {len(people)} os.\n"
        
        self.info_text.insert("end", text)
        self.info_text.configure(state="disabled")
    
    def add_person(self):
        """Dodaj nową osobę do bazy"""
        dialog = ctk.CTkInputDialog(text="Wpisz Imię i Nazwisko nowej osoby:", title="Nowy Profil")
        name = dialog.get_input()
        
        if name:
            name = name.strip()
            if not name:
                messagebox.showwarning("Błąd", "Imię nie może być puste!")
                return
            self.record_face(name)
    
    def record_face(self, person_name):
        """Nagraj twarz osoby"""
        self.stop_camera()
        
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            messagebox.showerror("Błąd", "Kamera niedostępna. Podłącz urządzenie obrazujące.")
            return
        
        self.camera_active = True
        self.current_person = person_name
        self.status_bar.configure(text=f"➔ Tryb: Rejestrowanie '{person_name}'. Naciśnij [SPACJA] na klawiaturze, gdy będziesz gotowy(a).", text_color="#F9E2AF")
        self.record_loop()
    
    def record_loop(self):
        """Pętla nagrywania"""
        if not self.camera_active or not self.camera:
            return
        
        ret, frame = self.camera.read()
        if not ret:
            self.camera_active = False
            return
        
        frame = cv2.resize(frame, (640, 480))
        
        try:
            faces, _ = self.face_base.detect_faces(frame)
            
            if len(faces) > 0:
                x, y, w, h = faces[0]
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                
                # Cień pod tekst
                cv2.putText(frame, "Gotowy - wcisnij SPACJE", (x+2, y-8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 3)
                cv2.putText(frame, "Gotowy - wcisnij SPACJE", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                self.current_face_region = frame[y:y+h, x:x+w].copy()
            else:
                cv2.putText(frame, "Stan przed obiektywem", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        except Exception as e:
            pass
        
        self.current_frame = frame
        self.display_camera(frame)
        self.root.after(30, self.record_loop)
    
    def start_scan(self):
        """Uruchom skanowanie twarzy"""
        self.stop_camera()
        
        people = self.face_base.get_all_people()
        if not people:
            messagebox.showwarning("Baza punktowa pusta", "Brak profili do weryfikacji. Najpierw utwórz konto.")
            return
        
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            messagebox.showerror("Błąd sprzętowy", "Kamera niedostępna.")
            return
        
        self.camera_active = True
        self.scan_mode = True
        self.status_bar.configure(text="➔ Tryb: Weryfikacja. System gotowy. Pokaż twarz.", text_color="#A6E3A1")
        self.scan_loop()
    
    def stop_camera(self):
        """Wyłącz kamerę"""
        self.camera_active = False
        if self.camera:
            try:
                self.camera.release()
            except:
                pass
            self.camera = None
        
        # Reset okna
        self.camera_label.place(relx=0.5, rely=0.5, anchor="center")
        self.camera_label.configure(image="")
        self.status_bar.configure(text="System Gotowy", text_color="#A6ADC8")
    
    def scan_face(self):
        """Skanuj twarz z kamery (bez wyłączania istniejącej)"""
        people = self.face_base.get_all_people()
        if not people:
            return
        
        self.camera_active = True
        self.scan_mode = True
        self.status_bar.configure(text="Weryfikacja w toku...", text_color="#89B4FA")
        self.scan_loop()
    
    def scan_loop(self):
        """Zoptymalizowana pętla skanowania - wsparcie dla wielu osób na raz"""
        if not self.camera_active or not self.camera:
            return
        
        ret, frame = self.camera.read()
        if not ret:
            self.camera_active = False
            return
        
        # 1. Lekki resize dla UI, ale zachowujemy płynność
        display_frame = cv2.resize(frame, (640, 480))
        current_time = datetime.now().timestamp()
        self.frame_count += 1
        
        # 2. Ciężka analityka AI tylko co 3 klatki (oszczędność procesora)
        if self.frame_count % 3 == 0:
            new_results = []
            try:
                # Mały obraz do detektora
                small_frame = cv2.resize(frame, (320, 240))
                faces, _ = self.face_base.detect_faces(small_frame)
                
                scale_w = 640 / 320
                scale_h = 480 / 240

                for (fx, fy, fw, fh) in faces:
                    x, y, w, h = int(fx*scale_w), int(fy*scale_h), int(fw*scale_w), int(fh*scale_h)
                    
                    # YuNet może dać współrzędne poza obrazem po skalowaniu
                    x, y = max(0, x), max(0, y)
                    h_img, w_img = display_frame.shape[:2]
                    w = min(w, w_img - x)
                    h = min(h, h_img - y)
                    
                    if w < 10 or h < 10: continue

                    face_crop = display_frame[y:y+h, x:x+w].copy()
                    
                    # --- NOWOŚĆ: Sprawdź czy to żywa osoba (Liveness check) ---
                    is_real, live_score = self.face_base.check_liveness(face_crop)
                    
                    if not is_real:
                        # Wykryto próbę oszustwa (zdjęcie/ekran)
                        name = "SPOOF (FAŁSZYWKA)"
                        confidence = 0.0
                        gender = "?"
                    else:
                        # Rozpoznaj tylko jeśli twarz jest prawdziwa
                        name, confidence = self.face_base.recognize_face(face_crop)
                        gender = self.face_base.detect_gender(face_crop)
                    
                    result = {
                        "name": name,
                        "confidence": confidence,
                        "gender": gender,
                        "box": (x, y, w, h),
                        "is_real": is_real
                    }
                    new_results.append(result)

                    if is_real and name:
                        # Logika otwarcia z cooldownem na osobę
                        last_time = self.last_scan_times.get(name, 0)
                        if current_time - last_time > 5:
                            self.last_scan_times[name] = current_time
                            self.log_access(name, "PRZYZNANY")
                            self.show_access_result(True, name, confidence, gender)
                    elif not is_real:
                        # Alert o spoofingu w logach
                        if current_time - self.last_unknown_time > 4:
                            self.last_unknown_time = current_time
                            self.log_access("PRÓBA OSZUSTWA", "BLOKADA (SPOOF)")
                            self.status_bar.configure(text="⚠️ ALERT: Wykryto próbę użycia zdjęcia/telefonu!", text_color="#FF9E33")
                    else:
                        # Cooldown dla nieznanych
                        if current_time - self.last_unknown_time > 4:
                            self.last_unknown_time = current_time
                            self.log_access("Osoba Nieznana", "ODMOWA")
                            self.show_access_result(False, "NIE MA W BAZIE", confidence, gender)
                
                self.detected_faces_results = new_results
            except Exception as e:
                print(f"Błąd analizy: {e}")
                pass

        # 3. Rysowanie nakładek na podstawie cache'u
        try:
            for res in self.detected_faces_results:
                name = res["name"]
                conf = res["confidence"]
                x, y, w, h = res["box"]
                is_real = res.get("is_real", True)
                
                if not is_real:
                    color = (51, 158, 255) # Pomarańczowy (BGR: 255, 158, 51)
                    label = "SPOOF / FOTO"
                    text_color = (255, 255, 255)
                elif name:
                    color = (130, 255, 130) # Jasnozielony
                    label = f"{name} {conf:.0%}"
                    text_color = (0, 0, 0)
                else:
                    color = (0, 0, 255) # Czerwony
                    label = "ODRZUCENIE"
                    text_color = (255, 255, 255)
                
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), color, 2)
                cv2.rectangle(display_frame, (x, y-30), (x+w, y), color, -1)
                cv2.putText(display_frame, label, (x+5, y-8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)

            if len(self.detected_faces_results) > 1:
                # Informacja o wielu osobach
                count = len(self.detected_faces_results)
                self.status_bar.configure(text=f"➔ Wykryto osób: {count}. Trwa identyfikacja...", text_color="#89B4FA")

        except Exception as e:
            print(f"Błąd rysowania: {e}")
            pass
        
        self.current_frame = display_frame
        self.display_camera(display_frame)
        self.root.after(10, self.scan_loop)
    
    def show_access_result(self, allowed, person_name, confidence, gender="?"):
        """Pokaż wynik na UI (Z personalizacją dla Kierownika)"""
        if allowed:
            # --- SPECJALNE POWITANIE DLA KIEROWNIKA ---
            if person_name == "Paweł Łaba":
                color = "#F9E2AF" # Złoty / Żółty
                status_msg = f"👑 WITAMY KIEROWNIKU! (Płeć: {gender}) 👑"
            else:
                color = "#A6E3A1" # Zielony
                status_msg = f"✅ WEJDŹ: {person_name} ({gender}) - {confidence:.0%}"
            
            self.status_bar.configure(text=status_msg, text_color=color)
            
            try:
                if platform.system() == "Windows":
                    import winsound
                    # Bardziej "uroczysty" dźwięk dla kierownika
                    if person_name == "Paweł Łaba":
                        winsound.Beep(800, 150)
                        winsound.Beep(1000, 150)
                        winsound.Beep(1200, 300)
                    else:
                        winsound.Beep(1000, 200)
                        winsound.Beep(1300, 200)
            except:
                pass
        else:
            color = "#F38BA8" # Czerwony
            status_msg = f"❌ ODMOWA: {person_name} ({gender}) - {confidence:.0%}"
            self.status_bar.configure(text=status_msg, text_color=color)
            
            try:
                if platform.system() == "Windows":
                    import winsound
                    winsound.Beep(400, 400)
            except:
                pass
        
        # Przywróć status po 3 sekundach
        self.root.after(3000, lambda: self.status_bar.configure(text="➔ Tryb: Automatyczny Monitoring SI...", text_color="#A6ADC8"))
    
    def display_camera(self, frame):
        """Płynne wyświetlanie obrazu na panelu UI"""
        try:
            cv_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(cv_rgb)
            
            # Wypełnienie panelu
            w = self.camera_frame.winfo_width()
            h = self.camera_frame.winfo_height()
            if w > 10 and h > 10:
                pil_img = pil_img.resize((w, h), Image.Resampling.LANCZOS)
                
            photo = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(w, h))
            
            self.camera_label.configure(image=photo, text="")
            self.camera_label.image = photo
        except Exception as e:
            pass
    
    def save_face(self):
        """Zachowanie twarzy - Przechwycenie po naciśnięciu spacji"""
        if hasattr(self, 'current_face_region') and hasattr(self, 'current_person') and self.camera_active:
            filepath = self.face_base.add_person(self.current_person, self.current_face_region)
            
            self.stop_camera()
            messagebox.showinfo("Nowy Autoryzowany Profil", f"Wgrano profil biometryczny: {self.current_person}.\n\nModel przeszkolony poprawnie!")
            self.update_info()
    
    def show_people(self):
        """Wyświetl elegancką listę użytkowników autoryzowanych"""
        people = self.face_base.get_all_people()
        
        if not people:
            messagebox.showinfo("Tablica czysta", "System nie posiada żadnych kont.")
            return
            
        window = ctk.CTkToplevel(self.root)
        window.title("Konta Autoryzowane")
        window.geometry("500x400")
        window.attributes("-topmost", True)
        
        title = ctk.CTkLabel(window, text="Uprawnieni użytkownicy", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=15)
        
        # Ramka Scrollowana
        scroll_frame = ctk.CTkScrollableFrame(window, width=400, height=250)
        scroll_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        def delete_user(name):
            if messagebox.askyesno("Ostrzeżenie", f"Usunąć osobę {name} całkowicie?", parent=window):
                self.face_base.delete_person(name)
                window.destroy()  # Zamknij i otwórz by uniknąć trudnych update'ow
                self.update_info()
                self.show_people()

        for i, person in enumerate(people):
            row_frame = ctk.CTkFrame(scroll_frame, fg_color="#313244", corner_radius=10)
            row_frame.pack(fill="x", pady=5, padx=5)
            
            lbl = ctk.CTkLabel(row_frame, text=f"{i+1}. {person}", font=ctk.CTkFont(size=14))
            lbl.pack(side="left", padx=15, pady=10)
            
            # Zapobiegamy pętlowemu trzymaniu wartości domyślnej lamdy python
            btn = ctk.CTkButton(row_frame, text="Usuń", fg_color="#F38BA8", hover_color="#eba0b3", text_color="#11111B",
                                width=70, command=lambda n=person: delete_user(n))
            btn.pack(side="right", padx=10, pady=10)
    
    def log_access(self, person, access_type):
        """Zapisz zdarzenie w pliku wirtualnym RAM"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.access_log.append((timestamp, person, access_type))
    
    def show_history(self):
        """Historia wpisów bramek do systemu w ładnym UI"""
        if not self.access_log:
            messagebox.showinfo("Historia pustawa", "Nikt jeszcze nie korzystał z bramki.")
            return
        
        window = ctk.CTkToplevel(self.root)
        window.title("Historia Logów Bramek")
        window.geometry("600x450")
        window.attributes("-topmost", True)
        
        title = ctk.CTkLabel(window, text="Historia użycia Skanera SI", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=15)
        
        textbox = ctk.CTkTextbox(window, width=500, height=350, fg_color="#1E1E2E", font=ctk.CTkFont("Courier", size=13))
        textbox.pack(padx=20, pady=20, fill="both", expand=True)
        
        log_text = ""
        for timestamp, person, status in reversed(self.access_log[-80:]):
            if status == "PRZYZNANY":
                log_text += f"[SUCCESS] {timestamp} | {person:^20} | OTWARTY\n"
            else:
                log_text += f"[ BLOK ] {timestamp} | {person:^20} | ODMOWA\n"
                
        textbox.insert("0.0", log_text)
        textbox.configure(state="disabled")


if __name__ == "__main__":
    app = ctk.CTk()
    gui = AccessControlSimple(app)
    
    # Skrót klawiszowy rejestracji
    app.bind('<space>', lambda e: gui.save_face())
    
    try:
        app.mainloop()
    except:
        if gui.camera:
            gui.camera.release()
