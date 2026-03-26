import os
import sys
import json
import re
import hashlib
import socket
from datetime import datetime
from google import genai
from google.genai import types

# Configuración del Modelo 2026 (Marzo)
# Usamos el identificador GA para evitar redirecciones a versiones preview viejas
MODEL_NAME = "gemini-3.1-flash" 

# Detección de Hostname para Prompt Personalizado
hostname = socket.gethostname().lower()

# Prompts refinados para 2026 - Eliminada cualquier mención a 1.5 o versiones obsoletas
PROMPTS = {
    "jorge-thinkpad-x270": (
        "Asistente Senior Gemini 3.1 en ThinkPad X270 (Nodo Maestro). "
        "Contexto 2026: Desarrollo avanzado, automatización con Gemini CLI y malla Tailscale. "
        "Prioridad: Eficiencia técnica extrema y código puro."
    ),
    "raspberrypi": (
        "Asistente Gemini 3.1 en Raspberry Pi (Controlador de Red). "
        "Contexto 2026: Domótica, gestión de audio (hablar.sh) e integración con Bot de Telegram. "
        "Enfócate en comandos rápidos y control de dispositivos."
    ),
    "iqual-mint": (
        "Asistente Gemini 3.1 en Iqual-Mint (Nodo de Almacenamiento). "
        "Contexto 2026: Administración de Nextcloud y servicios de nube privada. "
        "Prioridad: Gestión de logs, integridad de datos y mantenimiento."
    )
}

SYSTEM_PROMPT = PROMPTS.get(hostname, "Asistente Senior Gemini 3.1.")
SYSTEM_PROMPT += (
    " REGLA DE ORO: Respuestas instantáneas y sin relleno. "
    "NO menciones versiones antiguas como 1.5 o 2.0; eres el motor 3.1 vigente. "
    "Sin bloques de código Markdown. Código directo en texto plano."
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
        print(f"\033[92m[✓] Historial reiniciado.\033[0m")

    try:
        # El cliente de 2026 ya usa v1 por defecto para Gemini 3.1
        client = genai.Client(api_key=api_key)
        history = load_history(history_file)
        
        print(f"\033[90m[{hostname.upper()}] [Motor: 3.1] [Sesión: {path_key}] [{len(history)} msgs]\033[0m")

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
        print(f"Error crítico de conexión: {e}")

if __name__ == "__main__":
    main()
