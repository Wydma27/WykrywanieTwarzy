import requests
import cv2
import os
import time
from threading import Thread

class UnifiedNotifier:
    """Zintegrowany system powiadomień: Telegram, Discord, NTFY"""
    def __init__(self, telegram_token="", telegram_chat_id="", discord_webhook="", ntfy_topic=""):
        self.tg_token = telegram_token
        self.tg_chat = telegram_chat_id
        self.discord_url = discord_webhook
        self.ntfy_topic = ntfy_topic
        
        self.tg_active = bool(self.tg_token and self.tg_chat)
        self.discord_active = bool(self.discord_url)
        self.ntfy_active = bool(self.ntfy_topic)
        
        self.active = self.tg_active or self.discord_active or self.ntfy_active

    def send_message(self, message):
        """Wysyła tekst do wszystkich aktywnych kanałów (w tle)"""
        if not self.active: return
        Thread(target=self._send_all_msg, args=(message,)).start()

    def send_photo(self, frame, caption=""):
        """Wysyła zdjęcie do wszystkich kanałów (w tle)"""
        if not self.active: return
        
        # Zapisz tymczasowe zdjęcie
        temp_path = f"notify_{int(time.time())}.jpg"
        cv2.imwrite(temp_path, frame)
        
        Thread(target=self._send_all_photo, args=(temp_path, caption)).start()

    def _send_all_msg(self, msg):
        # 1. TELEGRAM
        if self.tg_active:
            try:
                r = requests.post(f"https://api.telegram.org/bot{self.tg_token}/sendMessage", 
                             json={"chat_id": self.tg_chat, "text": msg}, timeout=10)
                print(f"[NOTIFIER] Telegram Status: {r.status_code}")
                if r.status_code != 200: print(f"[NOTIFIER] Telegram Error: {r.text}")
            except Exception as e: print(f"[NOTIFIER] Telegram Exception: {e}")
            
        # 2. DISCORD
        if self.discord_active:
            try:
                r = requests.post(self.discord_url, json={"content": msg}, timeout=10)
                print(f"[NOTIFIER] Discord Status: {r.status_code}")
                if r.status_code not in [200, 204]: print(f"[NOTIFIER] Discord Error: {r.text}")
            except Exception as e: print(f"[NOTIFIER] Discord Exception: {e}")
            
        # 3. NTFY
        if self.ntfy_active:
            try:
                r = requests.post(f"https://ntfy.sh/{self.ntfy_topic}", data=msg.encode('utf-8'), timeout=10)
                print(f"[NOTIFIER] NTFY Status: {r.status_code}")
                if r.status_code != 200: print(f"[NOTIFIER] NTFY Error: {r.text}")
            except Exception as e: print(f"[NOTIFIER] NTFY Exception: {e}")

    def _send_all_photo(self, path, caption):
        # 1. TELEGRAM
        if self.tg_active:
            try:
                with open(path, 'rb') as f:
                    r = requests.post(f"https://api.telegram.org/bot{self.tg_token}/sendPhoto", 
                                 files={'photo': f}, data={'chat_id': self.tg_chat, 'caption': caption}, timeout=15)
                    print(f"[NOTIFIER] Telegram Photo Status: {r.status_code}")
            except Exception as e: print(f"[NOTIFIER] Telegram Photo Exception: {e}")

        # 2. DISCORD
        if self.discord_active:
            try:
                with open(path, 'rb') as f:
                    # Discord wymaga 'file' dla pliku i 'payload_json' lub 'content' dla tekstu
                    r = requests.post(self.discord_url, files={'file': f}, data={'content': caption}, timeout=15)
                    print(f"[NOTIFIER] Discord Photo Status: {r.status_code}")
            except Exception as e: print(f"[NOTIFIER] Discord Photo Exception: {e}")
            
        # 3. NTFY
        if self.ntfy_active:
            try:
                with open(path, 'rb') as f:
                    r = requests.put(f"https://ntfy.sh/{self.ntfy_topic}", data=f, 
                                headers={"Filename": "alert.jpg", "Title": caption}, timeout=15)
                    print(f"[NOTIFIER] NTFY Photo Status: {r.status_code}")
            except Exception as e: print(f"[NOTIFIER] NTFY Photo Exception: {e}")

        # Usuń plik
        try:
            if os.path.exists(path): os.remove(path)
        except: pass
