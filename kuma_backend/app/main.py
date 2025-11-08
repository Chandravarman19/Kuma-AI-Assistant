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
import traceback

# ============================================================
# ⚙️ ENV & CONFIG
# ============================================================
load_dotenv()

MEMORY_FILE = "memory.json"
TASK_FILE = "tasks.json"
MAX_MEMORY_ITEMS = 50
RECENT_MEMORIES_FOR_PROMPT = 5

MODEL = os.getenv("MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ============================================================
# 🚀 FastAPI Setup
# ============================================================
app = FastAPI(title="Kuma AI Assistant Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# 🧠 OpenAI Client
# ============================================================
client = OpenAI(api_key=OPENAI_API_KEY)

# ============================================================
# 📂 Memory System
# ============================================================
def load_json_file(file_path, default=None):
    if not os.path.exists(file_path):
        return default or []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default or []

def save_json_file(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_memory():
    return load_json_file(MEMORY_FILE, [])

def save_memory(mem):
    mem = mem[-MAX_MEMORY_ITEMS:]
    save_json_file(MEMORY_FILE, mem)

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

# ============================================================
# 🧾 To-Do Task System
# ============================================================
def load_tasks():
    return load_json_file(TASK_FILE, [])

def save_tasks(tasks):
    save_json_file(TASK_FILE, tasks)

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

# ============================================================
# 🔊 TTS (Voice Output)
# ============================================================
def speak_kuma(text: str):
    """Generate and play TTS audio safely"""
    try:
        speech = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=text
        )
        audio_stream = io.BytesIO()
        # speech.iter_bytes() may be used depending on SDK; using read() fallback if available
        try:
            # if response supports iter_bytes
            for chunk in speech.iter_bytes():
                audio_stream.write(chunk)
        except Exception:
            # try reading whole content
            try:
                audio_stream.write(speech.read())
            except Exception:
                pass
        audio_stream.seek(0)
        sound = AudioSegment.from_file(audio_stream, format="mp3")
        play(sound)
    except Exception as e:
        print(f"🎧 [Voice Error]: {e}")
        traceback.print_exc()

# ============================================================
# 🌦️ Weather Helper
# ============================================================
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

# ============================================================
# ⚙️ Local Command Handler
# ============================================================
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

    # 🧾 Tasks
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

    # 🎵 Music
    if "play song" in t or "play music" in t:
        music_path = os.path.join(os.path.expanduser("~"), "Music")
        os.startfile(music_path)
        return "Opening your music collection, Captain!"

    # 🌐 Sites
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

# ============================================================
# NEW: Conversation context (in-memory session)
# ============================================================
conversation_history = []  # list of {"role": "user"/"assistant", "content": "..."}
MAX_CONVERSATION_HISTORY = 12  # keep last N turns for context

def add_conversation(role: str, content: str):
    """Append to in-memory conversation history (role: 'user' or 'assistant')"""
    global conversation_history
    conversation_history.append({"role": role, "content": content, "time": datetime.now().isoformat()})
    # keep only last MAX_CONVERSATION_HISTORY entries
    conversation_history = conversation_history[-MAX_CONVERSATION_HISTORY:]

def clear_conversation():
    global conversation_history
    conversation_history = []

# ============================================================
# 🌊 Routes
# ============================================================
@app.get("/")
def home():
    return {"message": "🏴‍☠️ Kuma AI backend is sailing strong, Captain!"}

@app.get("/memory")
def view_memory():
    return {"memory": load_memory()}

@app.post("/memory/clear")
def api_clear_memory():
    clear_memory()
    return {"ok": True, "message": "Memory cleared."}

# NEW: endpoints for conversation
@app.get("/conversation")
def get_conversation():
    """Return current in-memory conversation history (useful for debugging)."""
    return {"conversation": conversation_history}

@app.post("/conversation/clear")
def api_clear_conversation():
    clear_conversation()
    return {"ok": True, "message": "Conversation cleared."}

@app.post("/query")
async def query(request: Request):
    data = await request.json()
    text = data.get("text", "").strip()

    if not text:
        return {"reply": "I didn’t hear anything, Captain. Can you repeat that?"}

    # Local check (unchanged behaviour)
    local_reply = local_handle(text)
    if local_reply:
        # speak locally and save to persistent memory as before
        try:
            speak_kuma(local_reply)
        except Exception:
            pass
        add_memory(f"User: {text}")
        add_memory(f"Kuma: {local_reply}")
        # also save to in-memory conversation for session context
        add_conversation("user", text)
        add_conversation("assistant", local_reply)
        return {"reply": local_reply}

    # -----------------------------
    # Build prompt with context:
    # - System personality prompt (same as before)
    # - Recent persistent memories (file-based) appended (optional)
    # - Recent in-memory conversation_history for session context
    # -----------------------------
    recent_mem = get_recent_memory()
    mem_text = ""
    if recent_mem:
        mem_text = "\nRecent memories:\n" + "\n".join([f"- {m['text']}" for m in recent_mem])

    system_prompt = (
        "You are Kuma — a loyal pirate AI assistant aboard the Thousand Sunny. "
        "You are cheerful, helpful, and always call the user 'Captain'. "
        "Keep replies short, witty, and natural like a friend at sea."
    )
    if mem_text:
        system_prompt += "\n\n" + mem_text

    # Build messages list: system + recent conversation (in-memory)
    messages = [{"role": "system", "content": system_prompt}]

    # Include session conversation history to preserve context
    for item in conversation_history:
        # conversation_history entries use 'role' keys 'user'/'assistant'
        messages.append({"role": item["role"], "content": item["content"]})

    # Finally append the new user message
    messages.append({"role": "user", "content": text})

    # Call OpenAI Chat Completion using current client (existing logic)
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.5,
            max_tokens=180
        )
        reply = response.choices[0].message.content.strip()

        # Speak the reply (same as before)
        try:
            speak_kuma(reply)
        except Exception:
            pass

        # Persist memory (same as before)
        add_memory(f"User: {text}")
        add_memory(f"Kuma: {reply}")

        # Add to in-memory conversation for future context
        add_conversation("user", text)
        add_conversation("assistant", reply)

        return {"reply": reply}

    except Exception as e:
        traceback.print_exc()
        fallback = local_handle(text)
        if fallback:
            try:
                speak_kuma(fallback)
            except Exception:
                pass
            # keep behavior consistent with older code
            add_memory(f"User: {text}")
            add_memory(f"Kuma: {fallback}")
            add_conversation("user", text)
            add_conversation("assistant", fallback)
            return {"reply": fallback}
        return {"reply": f"Error contacting AI: {e}"}
