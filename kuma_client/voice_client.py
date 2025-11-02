import requests
import speech_recognition as sr
import pyttsx3
import time
import sys
import webbrowser
from datetime import datetime
from win10toast import ToastNotifier  # notifications
import geocoder  # for IP-based location lookup

# 🌐 Backend API URLs
BASE_URL = "http://127.0.0.1:8000"
QUERY_URL = f"{BASE_URL}/query"
MEMORY_URL = f"{BASE_URL}/memory"
CLEAR_MEMORY_URL = f"{BASE_URL}/memory/clear"

# 🎙️ Text-to-Speech setup
engine = pyttsx3.init()
engine.setProperty("rate", 175)
engine.setProperty("volume", 1.0)

voices = engine.getProperty("voices")
if len(voices) > 0:
    engine.setProperty("voice", voices[0].id)  # [0]=male, [1]=female

# 🔔 Notification setup
notifier = ToastNotifier()


def notify(title, message):
    """Show a Windows desktop notification"""
    try:
        notifier.show_toast(title, message, duration=5, threaded=True)
    except Exception as e:
        print(f"⚠️ Notification error: {e}")


def speak(text, delay_after=0.4):
    """Speak text aloud with a short pause and send notification"""
    print(f"\n🧠 Onepiece: {text}")
    notify("🧠 Onepiece", text)
    engine.say(text)
    engine.runAndWait()
    time.sleep(delay_after)


def listen():
    """Capture user voice input"""
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 200
    recognizer.dynamic_energy_threshold = True

    with sr.Microphone() as source:
        print("\n🎙️  Listening... say 'Onepiece' to wake me.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source, phrase_time_limit=6)

    try:
        text = recognizer.recognize_google(audio)
        print(f"🗣️  You said: {text}")
        return text.lower()
    except sr.UnknownValueError:
        print("❌  I couldn’t understand that.")
        return ""
    except sr.RequestError:
        print("⚠️  Speech service error.")
        return ""


# ------------------------------------------------------------
# Weather helper (IP-based, using wttr.in)
# ------------------------------------------------------------
def get_weather():
    """Return simple weather string using wttr.in and IP-based city"""
    try:
        g = geocoder.ip('me')
        city = g.city or g.state or "your area"
    except Exception:
        city = "your area"

    try:
        # wttr.in quick format (e.g. "City: +20°C, Clear")
        resp = requests.get("https://wttr.in/?format=3", timeout=6)
        if resp.status_code == 200:
            # wttr returns a short single-line string like: "Location: +20°C, Clear"
            return f"The current weather for {city} is: {resp.text}, Captain."
        else:
            return f"Couldn't fetch weather right now for {city}, Captain."
    except Exception:
        return "Couldn't fetch the weather, Captain. Maybe the seas are rough."


# ------------------------------------------------------------
# Local offline handling (basic commands)
# ------------------------------------------------------------
def local_handle(text):
    t = text.lower()
    if "time" in t:
        return datetime.now().strftime("It's %I:%M %p, Captain.")
    if "date" in t:
        return datetime.now().strftime("Today is %A, %B %d, %Y, Captain.")
    if "weather" in t or "temperature" in t:
        return get_weather()
    if "joke" in t:
        return "Why did the pirate bring a bar of soap? Because he wanted to wash ashore! 😂"
    if "open youtube" in t:
        webbrowser.open("https://youtube.com")
        return "Opened YouTube for you, Captain."
    if "open tradingview" in t:
        webbrowser.open("https://www.tradingview.com")
        return "Opened TradingView for you, Captain."
    if "open steam" in t:
        webbrowser.open("steam://open/main")
        return "Attempting to open Steam, Captain."
    return None


# ------------------------------------------------------------
# Backend Communication
# ------------------------------------------------------------
def send_to_backend(command):
    """Send command to backend and return reply"""
    try:
        # include recent memory context to backend if available
        mem_text = ""
        try:
            mem_response = requests.get(MEMORY_URL, timeout=3)
            if mem_response.status_code == 200:
                memories = mem_response.json().get("memory", [])[-5:]
                if memories:
                    mem_text = "\n".join([f"- {m['text']}" for m in memories])
        except Exception:
            mem_text = ""

        payload_text = command
        if mem_text:
            payload_text = f"{command}\n\nRecent memories:\n{mem_text}"

        response = requests.post(QUERY_URL, json={"text": payload_text}, timeout=10)
        if response.status_code == 200:
            return response.json().get("reply", "").strip()
        else:
            return f"Server error {response.status_code}, Captain."
    except requests.exceptions.ConnectionError:
        fallback = local_handle(command)
        if fallback:
            return fallback
        return "Backend not reachable, Captain. Try starting the server."
    except Exception as e:
        fallback = local_handle(command)
        if fallback:
            return fallback
        return f"Error contacting backend: {e}"


def view_memory():
    """Retrieve and read all memories from backend"""
    try:
        response = requests.get(MEMORY_URL, timeout=5)
        if response.status_code != 200:
            return "Could not retrieve memory, Captain."

        data = response.json().get("memory", [])
        if not data:
            speak("I don't remember anything yet, Captain.")
            return None

        speak("Here's what I remember, Captain.")
        time.sleep(0.6)
        for m in data[-8:]:
            speak(m['text'], delay_after=0.8)
        speak("That’s all I remember for now, Captain!")
        return None
    except Exception:
        speak("Backend not reachable, Captain.")
        return None


def clear_memory():
    """Clear memories via backend"""
    try:
        response = requests.post(CLEAR_MEMORY_URL, timeout=5)
        if response.status_code == 200:
            return "All memories cleared, Captain. Fresh start!"
        return "Failed to clear memory, Captain."
    except Exception:
        return "Backend not reachable, Captain."


# ------------------------------------------------------------
# Main Loop
# ------------------------------------------------------------
def main():
    wake_words = ["onepiece", "one piece", "one peace", "on piece", "one peas"]
    speak("Aye aye, Captain! Onepiece is ready to sail!")

    while True:
        command = listen()

        # 🌀 Wake word
        if any(w in command for w in wake_words):
            speak("Aye aye, Captain! What’s the order?")
            time.sleep(1.2)
            cmd = listen()

            if not cmd:
                speak("Didn’t hear your command clearly, Captain.")
                continue

            # 💤 Exit
            if any(exit_word in cmd for exit_word in ["exit", "quit", "stop", "sleep"]):
                speak("Aye Captain, dropping anchor and going to sleep. See you soon!")
                sys.exit(0)

            # 🧠 Memory Recall
            if "what do you remember" in cmd or "memory" in cmd or "recall" in cmd:
                view_memory()
                continue

            # 🧹 Clear Memory
            if "clear memory" in cmd or "forget everything" in cmd:
                reply = clear_memory()
                speak(reply)
                continue

            # ⚙️ Send to AI or local
            reply = send_to_backend(cmd)
            speak(reply)


if __name__ == "__main__":
    main()
