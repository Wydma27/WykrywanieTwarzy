import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
from pathlib import Path
import numpy as np
from datetime import datetime
import platform
import json
import os

# Ustawienia CustomTkinter (Premium Palette)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Kolory Dashboardu (Catppuccin Mocha inspired)
COLORS = {
    "bg": "#11111B",
    "surface": "#1E1E2E",
    "overlay": "#313244",
    "text": "#CDD6F4",
    "accent_green": "#A6E3A1",
    "accent_blue": "#89B4FA",
    "accent_red": "#F38BA8",
    "accent_yellow": "#F9E2AF",
    "accent_mauve": "#CBA6F7",
    "accent_peach": "#FAB387"
}

# Import dźwięku
try:
    if platform.system() == "Windows":
        import winsound
except ImportError:
    pass

from face_base import FaceBase
from access_database import AccessDatabase
from notifier import UnifiedNotifier
from web_remote import SentinelWebDashboard
import socket # Do pobierania lokalnego adresu IP


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
        self.db = AccessDatabase()
        self.access_log = [] 
        self.strangers_dir = Path("strangers")
        self.strangers_dir.mkdir(exist_ok=True)
        
        # Zmienne stanu AI
        self.last_scan_times = {} 
        self.last_unknown_time = 0
        self.frame_count = 0
        self.detected_faces_results = [] # BRAKUJĄCY ATRYBUT - NAPRAWIONO
        
        # Powiadomienia (Multikanałowe)
        self.bot_token = ""
        self.chat_id = ""
        self.discord_webhook = ""
        self.ntfy_topic = ""
        
        # Wczytaj zapisane ustawienia
        self.load_settings()
        
        
        # Startuj Web Dashboard (Sentinel v6.1 Remote)
        self.web_server = SentinelWebDashboard(self, port=5000)
        self.web_server.start()
        
        self.notifier = UnifiedNotifier(self.bot_token, self.chat_id, self.discord_webhook, self.ntfy_topic)

        self.setup_ui()
        
        # Automatyczny start skanowania po uruchomieniu
        self.root.after(1000, self.start_scan)
    
    def setup_ui(self):
        """Nowoczesny, futurystyczny interfejs (Dojabebane UI)"""
        
        # --- KONFIGURACJA GRIDU ---
        self.root.configure(fg_color=COLORS["bg"])
        self.root.grid_columnconfigure(0, weight=0, minsize=250) # Sidebar
        self.root.grid_columnconfigure(1, weight=1)             # Main Content
        self.root.grid_rowconfigure(0, weight=1)

        # 1. BOCZNY PANEL (SIDEBAR)
        self.sidebar = ctk.CTkFrame(self.root, fg_color=COLORS["surface"], corner_radius=0, width=250)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        # Logo / Title w Sidebarze
        self.logo_label = ctk.CTkLabel(self.sidebar, text="🛡️ SENTINEL AI", 
                                       font=ctk.CTkFont(size=24, weight="bold"), text_color=COLORS["accent_green"])
        self.logo_label.pack(pady=(30, 10))
        
        self.version_label = ctk.CTkLabel(self.sidebar, text="v4.1 ENTERPRISE", 
                                          font=ctk.CTkFont(size=10), text_color=COLORS["accent_blue"])
        self.version_label.pack(pady=(0, 30))

        # Przyciski Nawigacyjne (Stylizowane)
        btn_opts = {"height": 45, "corner_radius": 10, "font": ctk.CTkFont(size=13, weight="bold")}
        
        self.btn_add = ctk.CTkButton(self.sidebar, text="➕ DODAJ UŻYTKOWNIKA", fg_color=COLORS["overlay"], 
                                     hover_color=COLORS["accent_green"], text_color=COLORS["text"],
                                     command=self.add_person, **btn_opts)
        self.btn_add.pack(fill="x", padx=20, pady=10)

        self.btn_scan = ctk.CTkButton(self.sidebar, text="🔍 SKANUJ TERAZ", fg_color=COLORS["accent_blue"], 
                                      hover_color="#74C7EC", text_color="#11111B",
                                      command=self.start_scan, **btn_opts)
        self.btn_scan.pack(fill="x", padx=20, pady=10)

        self.btn_stop = ctk.CTkButton(self.sidebar, text="⏹️ STOP", fg_color="#F38BA8", 
                                      hover_color="#eba0b3", text_color="#11111B",
                                      command=self.stop_camera, **btn_opts)
        self.btn_stop.pack(fill="x", padx=20, pady=10)

        self.btn_reset_cam = ctk.CTkButton(self.sidebar, text="🔄 RESET KAMERY", fg_color=COLORS["overlay"], 
                                           hover_color=COLORS["accent_peach"], text_color=COLORS["text"],
                                           command=self.start_scan, **btn_opts)
        self.btn_reset_cam.pack(fill="x", padx=20, pady=10)

        self.btn_strangers = ctk.CTkButton(self.sidebar, text="🕵️ GALERIA INTRUZÓW", fg_color=COLORS["overlay"], 
                                           hover_color=COLORS["accent_red"], text_color=COLORS["text"],
                                           command=self.show_strangers_gallery, **btn_opts)
        self.btn_strangers.pack(fill="x", padx=20, pady=10)

        # Ustawienia Powiadomień
        self.btn_notify = ctk.CTkButton(self.sidebar, text="📱 CENTRUM POWIADOMIEŃ", fg_color=COLORS["overlay"], 
                                         hover_color=COLORS["accent_mauve"], text_color=COLORS["text"],
                                         command=self.config_notifications, **btn_opts)
        self.btn_notify.pack(side="bottom", fill="x", padx=20, pady=10)
        
        self.btn_show_ip = ctk.CTkButton(self.sidebar, text="🌍 WEB MONITORING", fg_color=COLORS["overlay"], 
                                         hover_color=COLORS["accent_blue"], text_color=COLORS["text"],
                                         command=self.show_web_info, **btn_opts)
        self.btn_show_ip.pack(side="bottom", fill="x", padx=20, pady=30)

        # Statystyki w sidebarze
        self.stats_frame = ctk.CTkFrame(self.sidebar, fg_color=COLORS["overlay"], corner_radius=15)
        self.stats_frame.pack(fill="x", padx=20, pady=50)
        
        self.stats_title = ctk.CTkLabel(self.stats_frame, text="UŻYTKOWNICY:", font=ctk.CTkFont(size=12, weight="bold"))
        self.stats_title.pack(pady=(10, 0))
        
        self.people_count_lbl = ctk.CTkLabel(self.stats_frame, text="Ładowanie...", font=ctk.CTkFont(size=20, weight="bold"), 
                                            text_color=COLORS["accent_peach"])
        self.people_count_lbl.pack(pady=(0, 10))

        # 2. GŁÓWNY PANEL (DASHBOARD)
        self.main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_container.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)

        # Nagłówek Dashboardu
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color=COLORS["surface"], height=60, corner_radius=15)
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        self.header_title = ctk.CTkLabel(self.header_frame, text="MONITORING BIOMETRYCZNY LIVE", 
                                         font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["text"])
        self.header_title.pack(side="left", padx=30, pady=15)
        
        self.status_indicator = ctk.CTkLabel(self.header_frame, text="● SYSTEM ONLINE", 
                                             font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["accent_green"])
        self.status_indicator.pack(side="right", padx=30)
        self.animate_status()

        # Centrum Operacyjne (Kamera + Logi boczne)
        self.center_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.center_frame.grid(row=1, column=0, sticky="nsew")
        self.center_frame.grid_columnconfigure(0, weight=3)
        self.center_frame.grid_columnconfigure(1, weight=1)
        self.center_frame.grid_rowconfigure(0, weight=1)

        # OKNO KAMERY (Z "ramką" monitora)
        self.monitor_frame = ctk.CTkFrame(self.center_frame, fg_color=COLORS["surface"], corner_radius=20, border_width=2, border_color=COLORS["overlay"])
        self.monitor_frame.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        self.monitor_frame.pack_propagate(False)

        self.camera_label = ctk.CTkLabel(self.monitor_frame, text="OCZEKIWANIE NA SYGNAŁ...", 
                                         font=ctk.CTkFont(size=20, weight="bold"), text_color=COLORS["overlay"])
        self.camera_label.pack(expand=True, fill="both") # Changed place to pack for better centering and reliability

        # PANEL INFO (Prawy w Dashboardzie)
        self.info_panel = ctk.CTkFrame(self.center_frame, fg_color=COLORS["surface"], corner_radius=20)
        self.info_panel.grid(row=0, column=1, sticky="nsew")
        
        self.info_title = ctk.CTkLabel(self.info_panel, text="OSTATNIE REAKCJE", 
                                       font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["accent_mauve"])
        self.info_title.pack(pady=15)

        self.info_text = ctk.CTkTextbox(self.info_panel, fg_color="transparent", text_color=COLORS["text"], 
                                        font=ctk.CTkFont(family="Consolas", size=12))
        self.info_text.pack(fill="both", expand=True, padx=10, pady=(0, 15))

        # 3. DOLNY PASEK STATUSU
        self.bottom_bar = ctk.CTkFrame(self.main_container, fg_color=COLORS["surface"], height=50, corner_radius=15)
        self.bottom_bar.grid(row=2, column=0, sticky="ew", pady=(20, 0))
        
        self.status_bar = ctk.CTkLabel(self.bottom_bar, text="Przygotowanie komponentów AI...", 
                                       font=ctk.CTkFont(size=14), text_color=COLORS["text"])
        self.status_bar.pack(side="left", padx=20, pady=10)
        
        self.time_label = ctk.CTkLabel(self.bottom_bar, text="", font=ctk.CTkFont(size=14))
        self.time_label.pack(side="right", padx=20)
        self.update_clock()

        self.update_info()

    def update_clock(self):
        """Aktualizuj zegar w UI"""
        now = datetime.now().strftime("%H:%M:%S")
        self.time_label.configure(text=f"🕒 {now}")
        self.root.after(1000, self.update_clock)
    
    def load_settings(self):
        """Wczytaj ustawienia z pliku JSON"""
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r") as f:
                    data = json.load(f)
                    self.bot_token = data.get("bot_token", "")
                    self.chat_id = data.get("chat_id", "")
                    self.discord_webhook = data.get("discord_webhook", "")
                    self.ntfy_topic = data.get("ntfy_topic", "")
            except: pass

    def save_settings(self):
        """Zapisz ustawienia do pliku JSON"""
        data = {
            "bot_token": self.bot_token,
            "chat_id": self.chat_id,
            "discord_webhook": self.discord_webhook,
            "ntfy_topic": self.ntfy_topic
        }
        try:
            with open("config.json", "w") as f:
                json.dump(data, f)
        except: pass

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
        
        self.people_count_lbl.configure(text=f"{len(people)} osób") # UPDATE SIDEBAR COUNT
        self.info_text.insert("end", text)
        self.info_text.configure(state="disabled")

    def display_camera(self, frame):
        """Konwertuje klatkę OpenCV na format CTK i wyświetla w UI (DYNAMIKA)"""
        if frame is not None:
            try:
                # Konwersja BGR -> RGB
                rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_img)
                
                # Pobierz aktualny rozmiar monitora z UI
                w = self.monitor_frame.winfo_width()
                h = self.monitor_frame.winfo_height()
                
                # Jeśli okno jeszcze się nie wyrenderowało, użyj standardu
                if w < 100: w, h = 640, 480
                
                # Dopasowanie obrazu do okna
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(w, h))
                
                self.camera_label.configure(image=ctk_img, text="")
                self.camera_label.image = ctk_img 
            except Exception as e:
                pass
    
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
    
    def animate_status(self):
        """Efekt pulsowania wskaźnika online"""
        try:
            current_color = self.status_indicator.cget("text_color")
            new_color = COLORS["accent_green"] if current_color == COLORS["overlay"] else COLORS["overlay"]
            self.status_indicator.configure(text_color=new_color)
        except: pass
        self.root.after(800, self.animate_status)

    def record_face(self, person_name):
        """Nagraj twarz użytkownika (Wzmocniona inicjalizacja)"""
        self.stop_camera()
        print(f"[CAM] Nagrywanie użytkownika: {person_name}")
        
        for idx in [0, 1, 2]:
            self.camera = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if self.camera.isOpened():
                # Próba ustawienia rozdzielczości
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                ret, _ = self.camera.read()
                if ret: break
                self.camera.release()
            # Próba bez DSHOW
            self.camera = cv2.VideoCapture(idx)
            if self.camera.isOpened():
                ret, _ = self.camera.read()
                if ret: break
                self.camera.release()
        
        if not self.camera or not self.camera.isOpened():
            messagebox.showerror("Błąd", "Nie udało się uruchomić żadnej kamery!")
            return
        
        self.camera_active = True
        self.current_person = person_name
        self.status_bar.configure(text=f"➔ Tryb: Rejestrowanie '{person_name}'. Naciśnij [SPACJA] na klawiaturze.", text_color="#F9E2AF")
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
        """Uruchom skanowanie (Multi-mode Auto Detection)"""
        self.stop_camera()
        
        people = self.face_base.get_all_people()
        if not people:
            messagebox.showwarning("Baza pusta", "Najpierw dodaj Użytkownika.")
            return
        
        print("[SYSTEM] Szukanie stabilnego sygnału wideo...")
        found = False
        for idx in [0, 1, 2, 700]:
            # Tryb 1: DSHOW
            self.camera = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if self.camera.isOpened():
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                ret, _ = self.camera.read()
                if ret: 
                    print(f"[CAM] Stabilny sygnał na indeksie {idx} (DSHOW)")
                    found = True; break
                self.camera.release()
            
            # Tryb 2: Standard
            self.camera = cv2.VideoCapture(idx)
            if self.camera.isOpened():
                ret, _ = self.camera.read()
                if ret: 
                    print(f"[CAM] Stabilny sygnał na indeksie {idx} (STD)")
                    found = True; break
                self.camera.release()

        if not found:
            messagebox.showerror("BŁĄD KAMERY", "System nie może uzyskać obrazu. \n1. Sprawdź czy inna aplikacja nie używa kamery.\n2. Podłącz kamerę ponownie.")
            return
        
        self.camera_active = True
        self.scan_mode = True
        self.status_bar.configure(text="🛡️ MONITORING AKTYWNY | SYSTEM SENTINEL GOTOWY", text_color=COLORS["accent_green"])
        self.scan_loop()
    
    def stop_camera(self):
        """Wyłącz kamerę i wyczyść podgląd"""
        self.camera_active = False
        if self.camera:
            try:
                self.camera.release()
            except:
                pass
            self.camera = None
        
        # Reset okna
        self.camera_label.configure(image=None, text="OCZEKIWANIE NA SYGNAŁ...")
        # Ensure it's visible if it was moved
        self.camera_label.pack(expand=True, fill="both")
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
        if not self.camera_active or not self.camera or not self.camera.isOpened():
            return
        
        ret, frame = self.camera.read()
        
        # Jeśli raz nie odczytało, spróbuj jeszcze raz (warm-up kamery)
        if not ret:
            print("[CAM] Chwilowy brak klatki, ponawiam...")
            self.root.after(100, self.scan_loop)
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
                        emotion = self.face_base.detect_emotion(face_crop)
                    
                    result = {
                        "name": name,
                        "confidence": confidence,
                        "gender": gender,
                        "emotion": emotion,
                        "box": (x, y, w, h),
                        "is_real": is_real
                    }
                    new_results.append(result)

                    if is_real and name:
                        # Logika otwarcia z cooldownem na osobę
                        last_time = self.last_scan_times.get(name, 0)
                        if current_time - last_time > 5:
                            self.last_scan_times[name] = current_time
                            self.log_access(name, "PRZYZNANY", confidence, display_frame, gender, emotion) 
                            self.show_access_result(True, name, confidence, gender)
                    elif not is_real:
                        # Alert o spoofingu w logach
                        if current_time - self.last_unknown_time > 4:
                            self.last_unknown_time = current_time
                            self.log_access("PRÓBA OSZUSTWA", "BLOKADA (SPOOF)", 0.0, display_frame, "?") 
                            self.status_bar.configure(text="⚠️ ALERT: Wykryto próbę użycia zdjęcia/telefonu!", text_color="#FF9E33")
                    else:
                        # Cooldown dla nieznanych
                        if current_time - self.last_unknown_time > 4:
                            # --- SZTUCZNA INTELIGENCJA: Deduplikacja Intruzów ---
                            is_already_seen, stranger_feat = self.face_base.is_already_in_archive(face_crop)
                            
                            if not is_already_seen:
                                self.last_unknown_time = current_time
                                self.log_access("Osoba Nieznana", "ODMOWA", 0.0, display_frame, "?", emotion)
                                self.face_base.add_to_stranger_archive(stranger_feat) # Zapamiętaj intruza
                                self.show_access_result(False, "NIE ROZPOZNANO (ARCHIWIZACJA)", confidence, gender)
                            else:
                                # Ten gość już tu był - nie śpamiemy telefonem!
                                self.status_bar.configure(text="🕵️ INTRUZ POD OBSERWACJĄ (DUPLIKAT POMINIĘTY)", text_color=COLORS["accent_blue"])
                
                self.detected_faces_results = new_results
            except Exception as e:
                print(f"Błąd analizy: {e}")
                pass

        # 3. Rysowanie nakładek HUD
        try:
            # Cyberpunkowy Scan-line (Animacja)
            scan_y = (int(datetime.now().timestamp() * 100) % 480)
            cv2.line(display_frame, (0, scan_y), (640, scan_y), (100, 100, 100), 1)

            for res in self.detected_faces_results:
                name = res["name"]
                conf = res["confidence"]
                x, y, w, h = res["box"]
                is_real = res.get("is_real", True)
                
                # Ramka "celownika"
                color = (0, 255, 0) if is_real and name else (0, 0, 255)
                if not is_real: color = (51, 158, 255)

                # Narożniki HUD
                sz = 20
                cv2.line(display_frame, (x, y), (x+sz, y), color, 3)
                cv2.line(display_frame, (x, y), (x, y+sz), color, 3)
                cv2.line(display_frame, (x+w, y), (x+w-sz, y), color, 3)
                cv2.line(display_frame, (x+w, y), (x+w, y+sz), color, 3)
                cv2.line(display_frame, (x, y+h), (x+sz, y+h), color, 3)
                cv2.line(display_frame, (x, y+h), (x, y+h-sz), color, 3)
                cv2.line(display_frame, (x+w, y+h), (x+w-sz, y+h), color, 3)
                cv2.line(display_frame, (x+w, y+h), (x+w, y+h-sz), color, 3)

                # Etykieta
                g_short = "M" if res["gender"] == "Mezczyzna" else "K"
                label = f"{name} ({g_short}) {conf:.0%}" if name else "NIEZNANY / SPOOF"
                biometric = f"STAN EMOCJONALNY: {res['emotion']}"
                
                # Belka główna
                cv2.rectangle(display_frame, (x, y-45), (x+w, y), color, -1)
                cv2.putText(display_frame, label, (x+5, y-28), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 2)
                
                # Belka biometryczna (mniejsza)
                cv2.putText(display_frame, biometric, (x+5, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,0), 1)

            if len(self.detected_faces_results) > 1:
                cv2.putText(display_frame, f"CELI: {len(self.detected_faces_results)}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        except Exception as e:
            print(f"Błąd HUD: {e}")
        
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
    
    def log_access(self, person, access_type, confidence=1.0, current_frame=None, gender="?", emotion="?"):
        """Zapisz zdarzenie i wyślij powiadomienie (z wszystkimi danymi)"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.access_log.append((timestamp, person, access_type))
        
        # PERSYSTENCJA: Zapis do SQLite
        try:
            self.db.log_access(person, access_type, confidence)
        except Exception as e:
            print(f"Błąd bazy: {e}")

        # POWIADOMIENIE (Zawsze wysyłaj tylko ważne zdarzenia)
        if self.notifier.active:
            g_msg = f"płeć: {gender}, stan: {emotion}" if gender != "?" else ""
            
            if person == "Paweł Łaba":
                msg = f"👑 [WEJŚCIE] Kierownik Paweł Łaba ({g_msg}) wszedł o {timestamp}."
                self.notifier.send_message(msg)
                
            elif access_type == "PRZYZNANY":
                msg = f"✅ [WEJŚCIE] Użytkownik {person} ({g_msg}) został rozpoznany o {timestamp}."
                self.notifier.send_message(msg)
                
            elif access_type == "BLOKADA (SPOOF)":
                msg = f"❗ [ALERT] Próba oszustwa (SPOOFING) wykryta o {timestamp}!"
                if current_frame is not None:
                    self.notifier.send_photo(current_frame, caption=msg)
                else:
                    self.notifier.send_message(msg)
                    
            elif access_type == "ODMOWA":
                msg = f"⚠️ [NIE ROZPOZNANO] System wykrył twarz, ale NIE WYKRYWA jej w bazie danych! ({timestamp})"
                if current_frame is not None:
                    # Zapisz lokalnie w galerii intruzów
                    file_name = f"stranger_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    cv2.imwrite(str(self.strangers_dir / file_name), current_frame)
                    self.notifier.send_photo(current_frame, caption=msg)
                else:
                    self.notifier.send_message(msg)

    def config_notifications(self):
        """Nowoczesne okno ustawień dla wielu systemów powiadomień"""
        window = ctk.CTkToplevel(self.root)
        window.title("Multi-Channel Notifications Settings")
        window.geometry("500x550")
        window.attributes("-topmost", True)
        
        main_lbl = ctk.CTkLabel(window, text="USTAWIENIA ALARMÓW MOBILNYCH", font=ctk.CTkFont(size=20, weight="bold"))
        main_lbl.pack(pady=20)
        
        # --- TELEGRAM ---
        tg_frame = ctk.CTkFrame(window, fg_color=COLORS["surface"])
        tg_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(tg_frame, text="TELEGRAM BOT", text_color=COLORS["accent_blue"]).pack(pady=5)
        
        tg_token_entry = ctk.CTkEntry(tg_frame, placeholder_text="Bot API Token", width=400)
        tg_token_entry.insert(0, self.bot_token)
        tg_token_entry.pack(pady=5)
        
        tg_chat_entry = ctk.CTkEntry(tg_frame, placeholder_text="Chat ID", width=400)
        tg_chat_entry.insert(0, self.chat_id)
        tg_chat_entry.pack(pady=5)
        
        # --- DISCORD ---
        ds_frame = ctk.CTkFrame(window, fg_color=COLORS["surface"])
        ds_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(ds_frame, text="DISCORD WEBHOOK", text_color=COLORS["accent_mauve"]).pack(pady=5)
        
        ds_entry = ctk.CTkEntry(ds_frame, placeholder_text="Webhook URL (Discord)", width=400)
        ds_entry.insert(0, self.discord_webhook)
        ds_entry.pack(pady=5)
        
        # --- NTFY.SH ---
        nf_frame = ctk.CTkFrame(window, fg_color=COLORS["surface"])
        nf_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(nf_frame, text="NTFY.SH (NAJSZYBSZY - darmowy)", text_color=COLORS["accent_green"]).pack(pady=5)
        
        nf_entry = ctk.CTkEntry(nf_frame, placeholder_text="Nazwa Twojego kanału (Topic)", width=400)
        nf_entry.insert(0, self.ntfy_topic)
        nf_entry.pack(pady=5)

        def save_all():
            # POBIERZ DANE Z PÓL
            self.bot_token = tg_token_entry.get().strip()
            self.chat_id = tg_chat_entry.get().strip()
            self.discord_webhook = ds_entry.get().strip()
            self.ntfy_topic = nf_entry.get().strip()
            
            # ZAPISZ I WTŁOCZ DO NOTIFIERA
            self.save_settings()
            self.notifier = UnifiedNotifier(self.bot_token, self.chat_id, self.discord_webhook, self.ntfy_topic)
            messagebox.showinfo("Zapisano", "Ustawienia powiadomień zostały zaktualizowane i zapisane!")
            window.destroy()

        save_btn = ctk.CTkButton(window, text="ZAPISZ I AKTYWUJ SYSTEMY", fg_color=COLORS["accent_green"], 
                                  text_color="#11111B", font=ctk.CTkFont(weight="bold"), command=save_all)
        save_btn.pack(pady=30)
    
    def show_strangers_gallery(self):
        """Wyświetla okno z galerią zdjęć nieznanych osób (intruzów)"""
        window = ctk.CTkToplevel(self.root)
        window.title("Archiwum Intruzów - Sentinel AI")
        window.geometry("800x600")
        window.attributes("-topmost", True)
        
        title = ctk.CTkLabel(window, text="WYKRYTE OSOBY NIEZNANE", font=ctk.CTkFont(size=22, weight="bold"), text_color=COLORS["accent_red"])
        title.pack(pady=20)
        
        scroll_frame = ctk.CTkScrollableFrame(window, width=750, height=500, fg_color=COLORS["surface"])
        scroll_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        files = sorted(list(self.strangers_dir.glob("*.jpg")), reverse=True)
        
        if not files:
            ctk.CTkLabel(scroll_frame, text="Brak zarejestrowanych intruzów.", font=ctk.CTkFont(size=16)).pack(pady=50)
            return

        # Grid layout dla zdjęć
        cols = 3
        for i, img_path in enumerate(files):
            row = i // cols
            col = i % cols
            
            frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["overlay"], corner_radius=15)
            frame.grid(row=row, column=col, padx=10, pady=10)
            
            # Wczytaj i przeskaluj zdjęcie
            pil_img = Image.open(img_path)
            # Thumbnail
            img_w, img_h = pil_img.size
            ratio = 200 / img_w
            pil_img = pil_img.resize((200, int(img_h * ratio)))
            
            img_ctk = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(200, int(img_h * ratio)))
            
            lbl_img = ctk.CTkLabel(frame, image=img_ctk, text="")
            lbl_img.pack(padx=10, pady=(10, 5))
            
            # Data i godzina z nazwy pliku
            time_str = img_path.stem.replace("stranger_", "").replace("_", " ")
            lbl_time = ctk.CTkLabel(frame, text=time_str, font=ctk.CTkFont(size=10))
            lbl_time.pack(pady=(0, 5))
            
            def delete_photo(p=img_path, f=frame):
                if messagebox.askyesno("Usuń", "Czy na pewno usunąć to zdjęcie?"):
                    p.unlink()
                    f.destroy()
            
            btn_del = ctk.CTkButton(frame, text="USUŃ", fg_color=COLORS["accent_red"], height=25, width=100, 
                                     command=delete_photo)
            btn_del.pack(pady=5)

    def show_web_info(self):
        """Pokazuje instrukcję jak połączyć się z telefonem"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except: local_ip = "127.0.0.1"
        
        msg = f"🛰️ SENTINEL WEB BAZA 🛰️\n\nTo jest Twoja prywatna strona monitoringu.\nAby oglądać obraz ZDALNIE na telefonie, upewnij się,\nże telefon jest w tym samym WiFi co PC i wejdź na:\n\nhttp://{local_ip}:5000\n\nMożesz tam oglądać podgląd na żywo i blokować PC zdalnie."
        messagebox.showinfo("Monitoring Bezprzewodowy", msg)

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
