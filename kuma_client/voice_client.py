import requests
import speech_recognition as sr
import pyttsx3
import time

# Kuma backend URL
BACKEND_URL = "http://127.0.0.1:8000/query"

# Initialize TTS engine
engine = pyttsx3.init()
engine.setProperty("rate", 180)

def speak(text):
    """Convert text to speech"""
    print(f"Kuma 🧠: {text}")
    engine.say(text)
    engine.runAndWait()

def listen():
    """Listen and convert speech to text"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎙️  Listening... say 'Kuma' to wake me.")
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

def main():
    speak("Kuma is ready!")
    while True:
        command = listen()

        if "kuma" in command:
            speak("Yes, I’m listening.")
            time.sleep(2)
            cmd = listen()

            if cmd:
                try:
                    response = requests.post(BACKEND_URL, json={"text": cmd})
                    if response.status_code == 200:
                        reply = response.json().get("reply", "No reply received.")
                        speak(reply)
                    else:
                        speak(f"Server error {response.status_code}")
                except Exception as e:
                    speak(f"Connection error: {e}")

if __name__ == "__main__":
    main()
