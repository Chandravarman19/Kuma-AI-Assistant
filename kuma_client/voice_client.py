import requests
import speech_recognition as sr
import pyttsx3
import time
import sys
import webbrowser
from datetime import datetime
from win10toast import ToastNotifier
import geocoder
import os

# ============================================================
# ⚙️ CONFIG
# ============================================================
USE_CLOUD_AI = True   # ⬅️ False = fully offline mode
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-")
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TTS_VOICE = "alloy"
BASE_URL = "http://127.0.0.1:8000"

QUERY_URL = f"{BASE_URL}/query"
MEMORY_URL = f"{BASE_URL}/memory"
CLEAR_MEMORY_URL = f"{BASE_URL}/memory/clear"

# ============================================================
# 🗣️ TTS Setup
# ============================================================
engine = pyttsx3.init()
engine.setProperty("rate", 175)
engine.setProperty("volume", 1.0)
voices = engine.getProperty("voices")
if voices:
    engine.setProperty("voice", voices[0].id)

notifier = ToastNotifier()


def notify(title, message):
    """Windows toast notification"""
    try:
        notifier.show_toast(title, message, duration=4, threaded=True)
    except Exception as e:
        print(f"⚠️ Notification error: {e}")


def speak_pyttsx3(text):
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"⚠️ pyttsx3 failed: {e}")


def speak_openai_tts(text):
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        from pathlib import Path
        speech_path = Path("response.mp3")
        response = openai.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=OPENAI_TTS_VOICE,
            input=text
        )
        response.stream_to_file(speech_path)
        os.system(f'start {speech_path}')
    except Exception as e:
        print(f"⚠️ OpenAI TTS failed: {e}")
        speak_pyttsx3(text)


def speak(text, delay_after=0.4):
    print(f"\n🧠 Kuma: {text}")
    notify("🧠 Kuma", text)
    if USE_CLOUD_AI:
        speak_openai_tts(text)
    else:
        speak_pyttsx3(text)
    time.sleep(delay_after)


# ============================================================
# 🎙️ Speech Recognition
# ============================================================
def listen(prompt_msg="Listening..."):
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 200
    recognizer.dynamic_energy_threshold = True

    with sr.Microphone() as source:
        print(f"\n🎙️ {prompt_msg}")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source, phrase_time_limit=8)

    try:
        text = recognizer.recognize_google(audio)
        print(f"🗣️ You said: {text}")
        return text.lower()
    except sr.UnknownValueError:
        print("❌ Couldn’t understand.")
        return ""
    except sr.RequestError:
        print("⚠️ Speech service error.")
        return ""


# ============================================================
# 🌦️ Weather Helper
# ============================================================
def get_weather():
    try:
        g = geocoder.ip('me')
        city = g.city or g.state or "your area"
    except Exception:
        city = "your area"
    try:
        resp = requests.get("https://wttr.in/?format=3", timeout=6)
        if resp.status_code == 200:
            return f"The current weather in {city} is: {resp.text}"
        else:
            return f"Couldn't fetch weather for {city}."
    except Exception:
        return "Couldn't fetch weather right now."


# ============================================================
# ⚙️ Local Handling
# ============================================================
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
    if "open google" in t:
        webbrowser.open("https://www.google.com")
        return "Opened Google for you, Captain."
    return None


# ============================================================
# 🧠 Backend Communication
# ============================================================
def send_to_backend(command):
    try:
        response = requests.post(QUERY_URL, json={"text": command}, timeout=10)
        if response.status_code == 200:
            return response.json().get("reply", "").strip()
        else:
            return f"Server error {response.status_code}, Captain."
    except requests.exceptions.ConnectionError:
        fallback = local_handle(command)
        if fallback:
            return fallback
        return "Backend not reachable, Captain."
    except Exception as e:
        fallback = local_handle(command)
        if fallback:
            return fallback
        return f"Error contacting backend: {e}"


def view_memory():
    try:
        response = requests.get(MEMORY_URL, timeout=5)
        if response.status_code != 200:
            speak("Could not retrieve memory, Captain.")
            return
        data = response.json().get("memory", [])
        if not data:
            speak("I don't remember anything yet, Captain.")
            return
        speak("Here's what I remember, Captain.")
        time.sleep(0.6)
        for m in data[-8:]:
            speak(m['text'], delay_after=0.8)
        speak("That’s all I remember, Captain!")
    except Exception:
        speak("Backend not reachable, Captain.")


def clear_memory():
    try:
        response = requests.post(CLEAR_MEMORY_URL, timeout=5)
        if response.status_code == 200:
            return "All memories cleared, Captain. Fresh start!"
        return "Failed to clear memory, Captain."
    except Exception:
        return "Backend not reachable, Captain."


# ============================================================
# 🚀 MAIN LOOP (Now supports FREE TALK)
# ============================================================
def main():
    wake_words = ["onepiece", "one piece", "on piece", "one peas"]
    speak("Aye aye, Captain! Kuma AI is ready to sail!")

    while True:
        command = listen("🎙️ Waiting for wake word...")

        if any(w in command for w in wake_words):
            speak("Aye aye, Captain! I’m listening.")
            time.sleep(0.6)

            while True:
                cmd = listen("🎙️ You may speak freely, Captain (say 'sleep' to stop)...")

                if not cmd:
                    speak("Didn’t catch that, Captain.")
                    continue

                if any(exit_word in cmd for exit_word in ["sleep", "exit", "quit", "stop listening"]):
                    speak("Aye Captain, entering sleep mode.")
                    break

                if "what do you remember" in cmd or "memory" in cmd or "recall" in cmd:
                    view_memory()
                    continue

                if "clear memory" in cmd or "forget everything" in cmd:
                    reply = clear_memory()
                    speak(reply)
                    continue

                # 🧠 Free talk or task execution
                reply = send_to_backend(cmd)
                speak(reply)


if __name__ == "__main__":
    main()
