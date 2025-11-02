import tkinter as tk
from PIL import Image, ImageTk
import requests
import speech_recognition as sr
import pyttsx3
import time
import threading

# ---------------------------------------
# ⚙️ Config
# ---------------------------------------
BACKEND_URL = "http://127.0.0.1:8000/query"
LUFFY_IMG = "luffy.png"  # make sure this image has a transparent background (PNG)
WAKE_WORDS = ["onepiece", "one piece", "one peace", "on piece", "one peas"]

# ---------------------------------------
# 🔊 Voice Engine Setup
# ---------------------------------------
engine = pyttsx3.init()
engine.setProperty("rate", 175)
engine.setProperty("volume", 1.0)
voices = engine.getProperty("voices")
if len(voices) > 1:
    engine.setProperty("voice", voices[0].id)

def speak(text):
    pirate_text = text.replace("Captain", "Cap’n").replace("you", "ye").replace("your", "yer")
    print(f"🧠 Luffy: {pirate_text}")
    engine.say(pirate_text)
    engine.runAndWait()

# ---------------------------------------
# 🎙️ Voice Recognition
# ---------------------------------------
def listen():
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 200
    recognizer.dynamic_energy_threshold = True

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source, phrase_time_limit=6)
    try:
        text = recognizer.recognize_google(audio)
        print(f"🗣️ You said: {text}")
        return text.lower()
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return ""

# ---------------------------------------
# 🪄 GUI Setup
# ---------------------------------------
root = tk.Tk()
root.overrideredirect(True)  # no window border
root.wm_attributes('-transparentcolor', '#0b0c10')  # transparent background
root.attributes('-topmost', True)  # always on top
root.configure(bg='#0b0c10')
root.geometry("250x250+100+100")

# 🏴‍☠️ Load Luffy Image
img = Image.open(LUFFY_IMG).resize((230, 230))
photo = ImageTk.PhotoImage(img)
luffy_label = tk.Label(root, image=photo, bg="#0b0c10", bd=0)
luffy_label.pack()

# 💬 Status Label
status_label = tk.Label(root, text="🎙️ Say 'Onepiece' to wake me!",
                        fg="white", bg="#0b0c10", font=("Comic Sans MS", 10))
status_label.pack()

# 🧭 Dragging Feature
def start_drag(event):
    root.x = event.x
    root.y = event.y

def on_drag(event):
    x = root.winfo_pointerx() - root.x
    y = root.winfo_pointery() - root.y
    root.geometry(f"+{x}+{y}")

luffy_label.bind("<Button-1>", start_drag)
luffy_label.bind("<B1-Motion>", on_drag)

# ---------------------------------------
# 🔁 Assistant Logic
# ---------------------------------------
def run_assistant():
    speak("Luffy is ready, Cap’n! Let’s set sail!")
    while True:
        status_label.config(text="🎧 Listening for wake word...")
        root.update()

        command = listen()

        if any(w in command for w in WAKE_WORDS):
            status_label.config(text="☠️ Aye aye, Cap’n! What’s the order?")
            speak("Aye aye, Cap’n! What’s the order?")
            time.sleep(1)

            cmd = listen()
            if not cmd:
                speak("Didn’t catch that, Cap’n.")
                continue

            try:
                response = requests.post(BACKEND_URL, json={"text": cmd})
                if response.status_code == 200:
                    reply = response.json().get("reply", "").strip()
                    if reply:
                        speak(reply)
                        status_label.config(text=f"Luffy: {reply[:30]}...")
                    else:
                        speak("No response, Cap’n.")
                else:
                    speak(f"Server error {response.status_code}, Cap’n.")
            except Exception:
                speak("Network issue, Cap’n! I’ll try again.")
        time.sleep(0.5)

# ---------------------------------------
# 💀 Exit Button
# ---------------------------------------
exit_btn = tk.Button(root, text="✖", fg="red", bg="#0b0c10",
                     font=("Arial", 12, "bold"), bd=0, command=root.destroy)
exit_btn.place(x=220, y=5)

# Run assistant in background thread
threading.Thread(target=run_assistant, daemon=True).start()

root.mainloop()
