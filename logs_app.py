import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from datetime import datetime
from access_database import AccessDatabase
import os

# Ustawienia CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Kolory Dashboardu (Premium Palette)
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

class LogsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📊 Panel Monitoringu - Logi Dostępu")
        self.root.geometry("1100x750")
        self.root.configure(fg_color=COLORS["bg"])
        
        self.db = AccessDatabase()
        self.setup_ui()
        self.refresh_logs()
        
    def setup_ui(self):
        # Główny kontener grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        # 1. NAGŁÓWEK Z KARTAMI STATYSTYK
        self.stats_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.stats_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        for i in range(3): self.stats_frame.grid_columnconfigure(i, weight=1)

        # Karta: Wszystkie
        self.card_total = self.create_stat_card(self.stats_frame, 0, "WSZYSTKIE ZDARZENIA", "0", COLORS["accent_blue"])
        # Karta: Sukcesy
        self.card_success = self.create_stat_card(self.stats_frame, 1, "AUTORYZOWANE", "0", COLORS["accent_green"])
        # Karta: Blokady
        self.card_denied = self.create_stat_card(self.stats_frame, 2, "BLOKADY / SPOOF", "0", COLORS["accent_red"])

        # 2. PANEL GŁÓWNY (TABELA + AKCJE)
        self.main_content = ctk.CTkFrame(self.root, fg_color=COLORS["surface"], corner_radius=20)
        self.main_content.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(1, weight=1)

        # Pasek narzędzi wewnątrz panelu
        self.toolbar = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        
        self.header_lbl = ctk.CTkLabel(self.toolbar, text="DZIENNIK ZDARZEŃ BIOMETRYCZNYCH", 
                                      font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["text"])
        self.header_lbl.pack(side="left")

        self.btn_export = ctk.CTkButton(self.toolbar, text="📥 EXPORT RAPORTU", fg_color=COLORS["overlay"], 
                                        hover_color=COLORS["accent_peach"], text_color=COLORS["text"],
                                        command=self.export_logs, width=150)
        self.btn_export.pack(side="right", padx=10)

        self.btn_refresh = ctk.CTkButton(self.toolbar, text="🔄 ODŚWIEŻ", fg_color=COLORS["accent_blue"], 
                                         hover_color="#74C7EC", text_color="#11111B",
                                         command=self.refresh_logs, width=120, font=ctk.CTkFont(weight="bold"))
        self.btn_refresh.pack(side="right", padx=10)

        # Tabela
        self.table_container = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.table_container.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # Styl dla Treeview
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background=COLORS["surface"], foreground="white", fieldbackground=COLORS["surface"],
                        rowheight=40, font=("Segoe UI", 11), borderwidth=0)
        style.map("Treeview", background=[('selected', COLORS["overlay"])])
        style.configure("Treeview.Heading", background=COLORS["bg"], foreground="white", font=("Segoe UI", 12, "bold"))

        self.table = ttk.Treeview(self.table_container, columns=("czas", "osoba", "status", "pewnosc"), show="headings")
        self.table.heading("czas", text="GODZINA")
        self.table.heading("osoba", text="IDENTYFIKACJA")
        self.table.heading("status", text="STATUS DOSTĘPU")
        self.table.heading("pewnosc", text="PEWNOŚĆ AI")
        
        for col in ("czas", "osoba", "status", "pewnosc"): 
            self.table.column(col, anchor="center")

        self.table.pack(fill="both", expand=True, side="left")
        
        scrollbar = ttk.Scrollbar(self.table_container, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    def create_stat_card(self, parent, col, title, value, color):
        card = ctk.CTkFrame(parent, fg_color=COLORS["surface"], corner_radius=15, border_width=2, border_color=COLORS["overlay"])
        card.grid(row=0, column=col, padx=10, sticky="nsew")
        
        lbl_title = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12, weight="bold"), text_color=color)
        lbl_title.pack(pady=(15, 0))
        
        lbl_val = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=32, weight="bold"), text_color=COLORS["text"])
        lbl_val.pack(pady=(0, 15))
        return lbl_val

    def refresh_logs(self):
        # Czyścimy tabelę
        for item in self.table.get_children(): self.table.delete(item)
            
        try:
            logs = self.db.get_access_history(limit=200)
            
            total = len(logs)
            success = sum(1 for log in logs if log[2] == "PRZYZNANY")
            denied = total - success
            
            self.card_total.configure(text=str(total))
            self.card_success.configure(text=str(success))
            self.card_denied.configure(text=str(denied))
            
            for user, time, status, conf in logs:
                tag = "success" if status == "PRZYZNANY" else "danger"
                conf_val = f"{conf:.0%}" if conf else "N/A"
                self.table.insert("", "end", values=(time, user, status, conf_val), tags=(tag,))
                
            self.table.tag_configure("success", foreground=COLORS["accent_green"])
            self.table.tag_configure("danger", foreground=COLORS["accent_red"])
            
        except Exception as e:
            print(f"Błąd odświeżania: {e}")
        
    def refresh_logs(self):
        # Czyścimy tabelę
        for item in self.table.get_children():
            self.table.delete(item)
            
        try:
            logs = self.db.get_access_history(limit=100)
            self.lbl_count.configure(text=f"Ostatnie 100 zdarzeń | Razem: {len(logs)}")
            
            for user, time, status, conf in logs:
                # Kolorowanie statusów
                tag = "normal"
                if status == "PRZYZNANY": tag = "success"
                elif "BLOKADA" in status or "SPOOF" in status: tag = "danger"
                
                # Dodajemy do tabeli
                conf_str = f"{conf:.0%}" if conf else "N/A"
                self.table.insert("", "end", values=(time, user, status, conf_str), tags=(tag,))
                
            self.table.tag_configure("success", foreground="#A6E3A1")
            self.table.tag_configure("danger", foreground="#F38BA8")
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można pobrać logów: {e}")
            
    def export_logs(self):
        logs = self.db.get_access_history(limit=1000)
        if not logs:
            return
            
        filename = f"export_logow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"RAPORT ZDARZEŃ SYSTEMU BIOMETRYCZNEGO - {datetime.now()}\n")
                f.write("="*70 + "\n")
                f.write(f"{'CZAS':<20} | {'OSOBA':<25} | {'STATUS':<20} | {'AI %':<6}\n")
                f.write("-"*70 + "\n")
                for user, time, status, conf in logs:
                    f.write(f"{time:<20} | {user:<25} | {status:<20} | {conf:.0%}\n")
            
            messagebox.showinfo("Export", f"Pomyślnie wyeksportowano logi do pliku:\n{filename}")
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd exportu: {e}")

if __name__ == "__main__":
    app = ctk.CTk()
    gui = LogsApp(app)
    app.mainloop()
