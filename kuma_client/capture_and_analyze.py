# capture_and_analyze.py
import pygetwindow as gw
import pyautogui
import pytesseract
from PIL import Image
import requests
import time
import os
import sys
import pyttsx3

# adjust if your tesseract path is different:
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

BACKEND_QUERY = "http://127.0.0.1:8000/query"
TEMP_IMAGE = "active_window.png"

# simple TTS for replies (offline)
engine = pyttsx3.init()
engine.setProperty("rate", 165)
voices = engine.getProperty("voices")
if voices:
    engine.setProperty("voice", voices[0].id)

def capture_active_window(save_path=TEMP_IMAGE, delay=1.2):
    """Capture the currently active window and save to file."""
    win = gw.getActiveWindow()
    if not win:
        print("❌ No active window found.")
        return None, "No active window"
    # If window coordinates invalid (some apps), fallback to full screen
    try:
        left, top, right, bottom = win.left, win.top, win.right, win.bottom
        if right - left <= 0 or bottom - top <= 0:
            raise Exception("Invalid window bounds")
        img = pyautogui.screenshot(region=(left, top, right - left, bottom - top))
    except Exception as e:
        print(f"⚠️ Window capture failed: {e}. Falling back to full screen.")
        img = pyautogui.screenshot()
    img.save(save_path)
    print(f"✅ Screenshot saved: {save_path}  (window: {win.title})")
    return save_path, win.title

def ocr_image(image_path):
    """Return extracted text from image using Tesseract."""
    if not os.path.exists(image_path):
        return ""
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    return text.strip()

def send_to_backend(text):
    """POST OCR text to backend /query and return reply (string)."""
    try:
        payload = {"text": f"Screen read:\n{text}"}
        r = requests.post(BACKEND_QUERY, json=payload, timeout=20)
        if r.status_code == 200:
            return r.json().get("reply", "")
        else:
            return f"Server error {r.status_code}"
    except Exception as e:
        return f"Connection error: {e}"

def speak_text(text):
    print("\n🔊 Onepiece says:", text)
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print("TTS error:", e)

def capture_ocr_and_talk():
    img_path, title = capture_active_window()
    if not img_path:
        speak_text("I couldn't capture the window, Captain.")
        return

    ocr_text = ocr_image(img_path)
    if not ocr_text or len(ocr_text.strip()) == 0:
        speak_text("I couldn't find readable text on the screen, Captain.")
        print("OCR returned empty.")
        return

    print("\n🪪 Detected window title:", title)
    print("\n🧾 OCR snippet:\n", ocr_text[:700].replace("\n", " ") + ("..." if len(ocr_text) > 700 else ""))

    # Send to backend for AI understanding
    reply = send_to_backend(ocr_text)
    speak_text(reply)

if __name__ == "__main__":
    # small delay to let you switch to the target window if you want
    print("Capture will start in 2 seconds. Switch to the window you want Onepiece to read.")
    time.sleep(2)
    capture_ocr_and_talk()
