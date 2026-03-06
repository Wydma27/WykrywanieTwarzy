from flask import Flask, Response, render_template_string, request, send_file
import cv2
import threading
import os
import platform
import time
from datetime import datetime
from pathlib import Path
import io

class SentinelWebDashboard:
    """Cyberpunkowy panel webowy do zdalnego nadzoru"""
    def __init__(self, main_app, port=5000):
        self.app = Flask(__name__)
        self.main_app = main_app # Referencja do głównej klasy
        self.port = port
        self.run_thread = None
        self.active = False
        
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/')
        def index():
            # Wczytaj nowo wyodrębniony plik HTML
            template_path = Path("templates/dashboard.html")
            try:
                with open(template_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                return render_template_string(html_content)
            except Exception as e:
                return f"BŁĄD ŁADOWANIA INTERFEJSU: {e}"

        @self.app.route('/video_feed')
        def video_feed():
            return Response(self.generate_frames(),
                           mimetype='multipart/x-mixed-replace; boundary=frame')

        @self.app.route('/cmd/<action>')
        def handle_command(action):
            if action == "foto":
                 # Trigger w głównej aplikacji (zrobi zdjęcie i wyśle alert)
                self.main_app.log_access("ZDALNY_PODGLĄD", "MANUAL_SHOT", current_frame=self.main_app.current_frame)
                return {"status": "success", "msg": "Zdjęcie zostało wykonane i przesłane na telefon."}
            
            elif action == "lock":
                if platform.system() == "Windows":
                    os.system("rundll32.exe user32.dll,LockWorkStation")
                    return {"status": "success", "msg": "Stacja robocza została zablokowana."}
            return {"status": "error", "msg": "Nieznana komenda."}

    def generate_frames(self):
        """Generator strumienia klatek (MJPEG)"""
        while self.active:
            if self.main_app.current_frame is not None:
                # Konwertuj klatkę z OpenCV na JPEG
                ret, buffer = cv2.imencode('.jpg', self.main_app.current_frame)
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                time.sleep(0.1)

    def start(self):
        self.active = True
        self.run_thread = threading.Thread(target=self.run_server, daemon=True)
        self.run_thread.start()
        print(f"[WEB] Dashboard uruchomiony pod adresem: http://localhost:{self.port}")

    def run_server(self):
        # Wyłączamy logi Flask w konsoli by nie śmiecić
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        self.app.run(host='0.0.0.0', port=self.port, threaded=True)

    def stop(self):
        self.active = False
