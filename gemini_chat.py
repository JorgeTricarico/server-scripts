import os
import sys
import json
import re
import hashlib
import socket
from datetime import datetime
from google import genai
from google.genai import types

# Configuración del Modelo 2026
MODEL_NAME = "gemini-2.5-flash-lite"  # El modelo más eficiente y con mejor disponibilidad en 2026

# Detección de Hostname para Prompt Personalizado
hostname = socket.gethostname().lower()

PROMPTS = {
    "jorge-thinkpad-x270": (
        "Eres el asistente Senior en mi ThinkPad X270 (Nodo Principal). "
        "Contexto: Desarrollo, automatización con Gemini CLI y gestión de red Tailscale. "
        "Sé extremadamente técnico, conciso y directo al código."
    ),
    "raspberrypi": (
        "Eres el asistente en mi Raspberry Pi (Centro de Control). "
        "Contexto: Domótica, reproducción de música, TTS (hablar.sh) y Bot de Telegram. "
        "Ayúdame con scripts ligeros y comandos de control de hardware/multimedia."
    ),
    "iqual-mint": (
        "Eres el asistente en Iqual-Mint (Servidor de Archivos). "
        "Contexto: Gestión de Nextcloud, almacenamiento masivo y servicios web. "
        "Enfócate en administración de sistemas, logs y mantenimiento de servicios."
    )
}

# Prompt por defecto si no reconoce el host
SYSTEM_PROMPT = PROMPTS.get(hostname, "Eres mi asistente Senior de programación conciso.")
SYSTEM_PROMPT += (
    " REGLA CRÍTICA: Respuestas ultra-directas. Sin saludos ni intros. "
    "Sin bloques Markdown ```. Código directo."
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

    if should_restart and os.path.exists(history_file): os.remove(history_file)

    try:
        client = genai.Client(api_key=api_key)
        history = load_history(history_file)
        
        print(f"\033[90m[{hostname.upper()}] [Sesión: {path_key}] [{len(history)} msgs]\033[0m")

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
