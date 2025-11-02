from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import json
import webbrowser
from datetime import datetime
from openai import OpenAI
import requests
import geocoder
from pydub import AudioSegment
from pydub.playback import play
import io

# -------------------------
# ENV & CONFIG
# -------------------------
load_dotenv()

MEMORY_FILE = "memory.json"
MAX_MEMORY_ITEMS = 50
RECENT_MEMORIES_FOR_PROMPT = 5
TASK_FILE = "tasks.json"

# -------------------------
# FastAPI Setup
# -------------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# OpenAI Setup
# -------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("MODEL", "gpt-4o-mini")

# -------------------------
# Memory Handling
# -------------------------
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_memory(mem_list):
    mem_list = mem_list[-MAX_MEMORY_ITEMS:]
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem_list, f, ensure_ascii=False, indent=2)

def add_memory(text: str):
    mem = load_memory()
    entry = {"text": text, "time": datetime.now().isoformat()}
    mem.append(entry)
    save_memory(mem)
    return entry

def get_recent_memory(n=RECENT_MEMORIES_FOR_PROMPT):
    mem = load_memory()
    return mem[-n:] if mem else []

def clear_memory():
    save_memory([])
    return []

# -------------------------
# 🧩 To-Do Task Memory
# -------------------------
def load_tasks():
    if not os.path.exists(TASK_FILE):
        return []
    try:
        with open(TASK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_tasks(tasks):
    with open(TASK_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def add_task(task: str):
    tasks = load_tasks()
    tasks.append({"task": task, "time": datetime.now().isoformat()})
    save_tasks(tasks)
    return f"Aye Captain! I’ve added: '{task}' to your to-do list."

def view_tasks():
    tasks = load_tasks()
    if not tasks:
        return "No tasks in your list yet, Captain!"
    lines = [f"- {t['task']}" for t in tasks[-10:]]
    return "Here’s your task list, Captain:\n" + "\n".join(lines)

def clear_tasks():
    save_tasks([])
    return "All tasks cleared, Captain!"

# -------------------------
# 🎙️ Luffy-style Voice Output
# -------------------------
def speak_luffy_style(text: str):
    """Generate and play AI speech that sounds lively like Luffy."""
    try:
        speech = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",  # replace later if official Luffy voice appears
            input=f"{text} Yohoho Captain!"
        )
        audio_data = io.BytesIO(speech.read())
        sound = AudioSegment.from_file(audio_data, format="mp3")
        play(sound)
    except Exception as e:
        print(f"🎧 [Voice Error]: {e}")

# -------------------------
# 🌦️ Weather Helper
# -------------------------
def get_weather():
    """Fetch simple weather info using wttr.in"""
    try:
        g = geocoder.ip("me")
        city = g.city or g.state or "your area"
    except Exception:
        city = "your area"

    try:
        resp = requests.get("https://wttr.in/?format=3", timeout=6)
        if resp.status_code == 200:
            return f"The weather in {city} is: {resp.text}, Captain."
        else:
            return f"Couldn't fetch weather for {city}, Captain."
    except Exception:
        return "Couldn't fetch the weather right now, Captain."

# -------------------------
# ⚙️ Local Command Handler
# -------------------------
def local_handle(text: str):
    t = text.lower()

    # 🧠 Memory
    if t.startswith("remember ") or " remember " in t:
        idx = t.find("remember")
        fact = text[idx + len("remember"):].strip(" .,")
        if not fact:
            return "What should I remember, Captain?"
        add_memory(fact)
        return f"I'll remember: {fact}"

    if "what do you remember" in t or "what do you know" in t or "what did i tell you" in t:
        mem = load_memory()
        if not mem:
            return "I don't remember anything yet, Captain."
        lines = [f"- {m['text']}" for m in mem[-8:]]
        return "I remember:\n" + "\n".join(lines)

    # 🧾 To-Do Tasks
    if "add task" in t or "remind me to" in t:
        task = text.split("to")[-1].strip(" .")
        if not task:
            return "What should I remind you about, Captain?"
        return add_task(task)

    if "show tasks" in t or "what are my tasks" in t or "show reminders" in t:
        return view_tasks()

    if "clear tasks" in t or "delete all tasks" in t:
        return clear_tasks()

    # 🕒 Utilities
    if "time" in t:
        return datetime.now().strftime("It's %I:%M %p, Captain.")
    if "date" in t:
        return datetime.now().strftime("Today is %A, %B %d, %Y, Captain.")
    if "weather" in t or "temperature" in t:
        return get_weather()
    if "joke" in t:
        return "Why did the pirate bring a bar of soap? Because he wanted to wash ashore! 😂"

    # ⚓ App shortcuts
    if "open youtube" in t:
        webbrowser.open("https://youtube.com")
        return "Opened YouTube for you, Captain."
    if "open tradingview" in t or "tradingview" in t:
        webbrowser.open("https://www.tradingview.com")
        return "Opened TradingView for you, Captain."
    if "open steam" in t:
        webbrowser.open("steam://open/main")
        return "Attempting to open Steam, Captain."
    if "open chrome" in t:
        os.system("start chrome")
        return "Opening Chrome, Captain!"
    if "open notepad" in t:
        os.system("start notepad")
        return "Opening Notepad, Captain!"
    if "open vs code" in t or "open visual studio code" in t:
        os.system("code")
        return "Opening VS Code, Captain!"
    if "shutdown" in t or "turn off" in t:
        os.system("shutdown /s /t 5")
        return "Shutting down the ship in 5 seconds, Captain!"

    # 🗂️ Folder shortcuts
    folders = {
        "downloads": "Downloads",
        "documents": "Documents",
        "desktop": "Desktop",
        "music": "Music",
        "pictures": "Pictures"
    }
    for key, folder in folders.items():
        if f"open {key}" in t:
            path = os.path.join(os.path.expanduser("~"), folder)
            os.startfile(path)
            return f"Opened {folder} folder, Captain!"

    # 🎵 Play music
    if "play song" in t or "play music" in t:
        music_path = os.path.join(os.path.expanduser("~"), "Music")
        os.startfile(music_path)
        return "Opening your music collection, Captain!"

    # 🌐 Websites
    sites = {
        "google": "https://www.google.com",
        "reddit": "https://www.reddit.com",
        "x": "https://x.com",
        "twitter": "https://x.com",
        "gmail": "https://mail.google.com"
    }
    for key, url in sites.items():
        if f"open {key}" in t:
            webbrowser.open(url)
            return f"Opened {key.capitalize()} for you, Captain!"

    return None

# -------------------------
# ⚡ FastAPI Routes
# -------------------------
@app.get("/")
def home():
    return {"message": "🏴‍☠️ Onepiece backend is running strong, Captain!"}

@app.get("/memory")
def view_memory():
    return {"memory": load_memory()}

@app.post("/memory/clear")
def api_clear_memory():
    clear_memory()
    return {"ok": True, "message": "Memory cleared."}

@app.post("/query")
async def query(request: Request):
    data = await request.json()
    text = data.get("text", "").strip()

    if not text:
        return {"reply": "I didn’t hear anything, Captain. Can you repeat that?"}

    # 🧠 Local handling
    local = local_handle(text)
    if local:
        speak_luffy_style(local)
        return {"reply": local}

    # 🧩 Add memory context
    recent_mem = get_recent_memory()
    mem_text = ""
    if recent_mem:
        mem_text = "Recent memories:\n" + "\n".join([f"- {m['text']}" for m in recent_mem])

    # 🧠 AI personality
    system_prompt = (
        "You are Onepiece — a lively, pirate-themed AI inspired by Monkey D. Luffy. "
        "You are the user's helpful personal assistant; call them 'Captain'. "
        "Keep replies short, fun, and slightly goofy — like a cheerful pirate."
    )
    if mem_text:
        system_prompt += "\n\n" + mem_text

    # 🌊 Call OpenAI
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            max_tokens=150,
            temperature=0.4
        )
        reply = response.choices[0].message.content.strip()
        speak_luffy_style(reply)
        return {"reply": reply}

    except Exception as e:
        fallback = local_handle(text)
        if fallback:
            speak_luffy_style(fallback)
            return {"reply": fallback}
        return {"reply": f"Error contacting AI: {str(e)}"}
