import os
import sys
import json
import re
import hashlib
import socket
import platform
from datetime import datetime
from google import genai
from google.genai import types

# Configuración del Modelo - Usamos el más avanzado disponible
MODEL_NAME = "gemini-3.1-flash-lite-preview" 

# --- CONTEXTO DINÁMICO ---
hostname = socket.gethostname().lower()
now = datetime.now()
data_context = {
    "year": now.year,
    "date": now.strftime("%d/%m/%Y %H:%M:%S"),
    "os": platform.platform(),
    "python_version": platform.python_version(),
    "node": hostname.upper()
}

PROMPTS = {
    "jorge-thinkpad-x270": "Nodo Maestro de Desarrollo. Enfoque: Automatización, Git, Tailscale y Gemini CLI.",
    "raspberrypi": "Nodo de Control Multimedia. Enfoque: Domótica, TTS (hablar.sh), Música y Bot Telegram.",
    "iqual-mint": "Nodo de Almacenamiento. Enfoque: Servidor Nextcloud, Backup e integridad de datos."
}

# Construcción del System Prompt Dinámico
base_prompt = PROMPTS.get(hostname, "Asistente Senior Multi-dispositivo.")
SYSTEM_PROMPT = (
    f"SISTEMA: {data_context['node']} | FECHA: {data_context['date']} | OS: {data_context['os']}\n"
    f"CONTEXTO: {base_prompt}\n"
    f"REGLA CRÍTICA: Eres Gemini 3.1. Respuestas directas, sin intros, sin markdown ```. "
    f"Estás en el año {data_context['year']}. Olvida versiones obsoletas (1.5, 2.0)."
)

CHAT_DIR = os.path.expanduser("~/.gemini_chat")
SESSIONS_DIR = os.path.join(CHAT_DIR, "sessions")
GLOBAL_SESSION_FILE = os.path.join(SESSIONS_DIR, "global_session.json")
os.makedirs(SESSIONS_DIR, exist_ok=True)

def clean_markdown(text):
    text = re.sub(r'```[a-zA-Z0-9_-]*\s*\n', '', text)
    text = re.sub(r'```', '', text)
    return text

def load_history(history_file):
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r") as f:
                data = json.load(f)
                for msg in data:
                    history.append(types.Content(role=msg["role"], parts=[types.Part.from_text(msg["text"])]))
        except Exception: pass
    return history

def save_history(chat, history_file):
    new_history = []
    try:
        for msg in chat.get_history():
            if msg.parts and hasattr(msg.parts[0], 'text'):
                new_history.append({"role": msg.role, "text": msg.parts[0].text})
        with open(history_file, "w") as f:
            json.dump(new_history, f)
    except Exception: pass

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    args = sys.argv[1:]
    is_global = "-g" in args or "--global" in args
    should_restart = "-r" in args or "--restart" in args
    clean_args = [a for a in args if a not in ["-g", "--global", "-r", "--restart"]]
    
    cwd = os.getcwd()
    path_key = "GLOBAL" if is_global else cwd
    history_file = GLOBAL_SESSION_FILE if is_global else os.path.join(SESSIONS_DIR, f"{hashlib.md5(cwd.encode()).hexdigest()}.json")

    if should_restart and os.path.exists(history_file): 
        os.remove(history_file)
        print(f"\033[92m[✓] Reset: {path_key}\033[0m")

    try:
        client = genai.Client(api_key=api_key)
        history = load_history(history_file)
        print(f"\033[90m[{data_context['node']}] [{data_context['date']}] [H:{len(history)}]\033[0m")

        chat = client.chats.create(
            model=MODEL_NAME,
            history=history,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
        )

        prompt = " ".join(clean_args)
        if not prompt.strip():
            while True:
                try: user_input = input("> ")
                except (EOFError, KeyboardInterrupt): print(); break
                if user_input.lower() in ["exit", "quit"]: break
                res = chat.send_message(user_input)
                print("\n" + clean_markdown(res.text) + "\n")
                save_history(chat, history_file)
        else:
            res = chat.send_message(prompt)
            print("\n" + clean_markdown(res.text) + "\n")
            save_history(chat, history_file)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
