# temp_listen_test.py
import speech_recognition as sr

r = sr.Recognizer()
mic = sr.Microphone()

print("Adjusting for ambient noise (1 sec)...")
with mic as source:
    r.adjust_for_ambient_noise(source, duration=1)
    print("Ready. Say something (10s)..")

with mic as source:
    audio = r.listen(source, phrase_time_limit=10)

try:
    text = r.recognize_google(audio)
    print("RECOGNIZED TEXT:", text)
except sr.UnknownValueError:
    print("Could not understand audio (UnknownValueError).")
except sr.RequestError as e:
    print("Could not request results from Google STT; check internet:", e)
