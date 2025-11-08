import tkinter as tk
from PIL import Image, ImageTk, ImageEnhance
import requests
import speech_recognition as sr
import pyttsx3
import threading
import time

# ---------------------------------------
# ⚙️ Config
# ---------------------------------------
BACKEND_URL = "http://127.0.0.1:8000/query"
LUFFY_IMG = "luffy.png"
WAKE_WORDS = ["onepiece", "one piece", "one peace", "on piece", "one peas"]
STOP_WORDS = ["stop", "bye", "sleep", "that’s all", "that's all"]

# ---------------------------------------
# 🔊 Voice Engine
# ---------------------------------------
engine = pyttsx3.init()
engine.setProperty("rate", 180)
engine.setProperty("volume", 1.0)

voices = engine.getProperty("voices")
if voices:
    engine.setProperty("voice", voices[0].id)

def speak(text):
    """Make Luffy speak like a pirate"""
    pirate_text = (
        text.replace("Captain", "Cap’n")
            .replace("you", "ye")
            .replace("your", "yer")
    )
    print(f"🧠 Luffy: {pirate_text}")
    engine.say(pirate_text)
    engine.runAndWait()

# ---------------------------------------
# 🎙️ Speech Recognition
# ---------------------------------------
def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.7)
        print("🎧 Listening...")
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
root.overrideredirect(True)
root.attributes('-topmost', True)
root.wm_attributes('-transparentcolor', '#0b0c10')
root.configure(bg='#0b0c10')
root.geometry("260x270+100+100")

# 🏴‍☠️ Load image
base_img = Image.open(LUFFY_IMG).resize((230, 230))
photo = ImageTk.PhotoImage(base_img)
luffy_label = tk.Label(root, image=photo, bg="#0b0c10", bd=0)
luffy_label.pack(pady=(5, 0))

# 💬 Status + dialogue label
status_label = tk.Label(root, text="🎙️ Say 'Onepiece' to wake me!",
                        fg="white", bg="#0b0c10", font=("Comic Sans MS", 10))
status_label.pack(pady=(5, 0))

dialogue_label = tk.Label(root, text="", fg="lightblue",
                          bg="#0b0c10", font=("Comic Sans MS", 9), wraplength=240, justify="center")
dialogue_label.pack(pady=(2, 0))

# ---------------------------------------
# 🧭 Draggable window
# ---------------------------------------
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
# ⚡ Animation effects
# ---------------------------------------
def animate_glow(active=True):
    """Simple brightness pulse animation to simulate talking/listening"""
    enhancer = ImageEnhance.Brightness(base_img)
    factor = 1.2 if active else 1.0
    img = enhancer.enhance(factor)
    frame = ImageTk.PhotoImage(img)
    luffy_label.configure(image=frame)
    luffy_label.image = frame

# ---------------------------------------
# 🤖 Assistant Logic
# ---------------------------------------
def query_backend(cmd):
    try:
        res = requests.post(BACKEND_URL, json={"text": cmd}, timeout=30)
        if res.status_code == 200:
            return res.json().get("reply", "")
        return f"Server error {res.status_code}, Cap’n!"
    except Exception as e:
        return f"Network error, Cap’n! ({e})"

def run_assistant():
    speak("Luffy is on deck! Waiting for yer orders, Cap’n!")
    while True:
        # 💤 Waiting for wake word
        status_label.config(text="🎧 Listening for wake word...")
        animate_glow(False)
        root.update()

        command = listen()
        if any(w in command for w in WAKE_WORDS):
            speak("Aye aye, Cap’n! I’m all ears! Let’s chat!")
            status_label.config(text="☠️ Chat mode active! Say 'stop' to end.")
            animate_glow(True)
            root.update()

            # 💬 Continuous conversation loop
            while True:
                cmd = listen()
                if not cmd:
                    continue

                # 💤 Stop words
                if any(x in cmd for x in STOP_WORDS):
                    speak("Aye Cap’n, I’ll rest for now!")
                    status_label.config(text="💤 Sleeping... Say 'Onepiece' to wake me.")
                    animate_glow(False)
                    break

                dialogue_label.config(text=f"🗣️ {cmd}")
                status_label.config(text="⚙️ Thinking...")
                root.update()

                reply = query_backend(cmd)
                dialogue_label.config(text=f"💬 {reply[:120]}...")
                speak(reply)
                animate_glow(True)
                root.update()

        time.sleep(0.5)

# ---------------------------------------
# 💀 Exit Button
# ---------------------------------------
exit_btn = tk.Button(root, text="✖", fg="red", bg="#0b0c10",
                     font=("Arial", 12, "bold"), bd=0, command=root.destroy)
exit_btn.place(x=230, y=5)

# ---------------------------------------
# 🚀 Start
# ---------------------------------------
threading.Thread(target=run_assistant, daemon=True).start()
root.mainloop()
