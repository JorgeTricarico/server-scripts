import os
import sys
import json
import re
import hashlib
from datetime import datetime
from google import genai
from google.genai import types

# Configuración
MODEL_NAME = "gemini-2.0-flash"  # Actualizado a una versión estable y rápida
SYSTEM_PROMPT = (
    "Eres mi colega Senior de programación. Te hablo desde la terminal de mi ThinkPad X270. "
    "REGLA CRÍTICA: Tus respuestas DEBEN ser extremadamente concisas y directas. "
    "NUNCA des introducciones, saludos, ni conclusiones largas. Ve directamente al código. "
    "Estás respondiendo en una consola de texto pura, el espacio es limitado. "
    "NO utilices bloques de código Markdown (```bash). Escribe el código directamente. "
    "Si te pido un comando, dame solo eso y una explicación de 1 línea máximo."
)

CHAT_DIR = os.path.expanduser("~/.gemini_chat")
SESSIONS_DIR = os.path.join(CHAT_DIR, "sessions")
INDEX_FILE = os.path.join(CHAT_DIR, "index.json")
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

def show_help():
    print("""
\033[94mChat con Gemini - Ayuda\033[0m
Uso: \033[93mchat [opciones] [mensaje]\033[0m

\033[94mOpciones:\033[0m
  \033[93m-h, --help\033[0m       Muestra esta ayuda.
  \033[93m-r, --restart\033[0m    Borra el historial de la sesión actual.
  \033[93m-g, --global\033[0m     Usa la sesión global (compartida entre carpetas).
  \033[93m-s, --sessions\033[0m   Lista sesiones guardadas.

\033[94mComandos interactivos:\033[0m
  \033[93mexit\033[0m             Salir.
  \033[93m/restart\033[0m         Reiniciar sesión.
  \033[93m/help\033[0m            Ver esta ayuda.
""")

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY no configurada.")
        sys.exit(1)

    args = sys.argv[1:]
    if "-h" in args or "--help" in args:
        show_help(); sys.exit(0)

    is_global = "-g" in args or "--global" in args
    should_restart = "-r" in args or "--restart" in args or "restart" in args
    
    clean_args = [a for a in args if a not in ["-g", "--global", "-r", "--restart", "restart"]]
    
    cwd = os.getcwd()
    path_key = "GLOBAL" if is_global else cwd
    history_file = GLOBAL_SESSION_FILE if is_global else os.path.join(SESSIONS_DIR, f"{hashlib.md5(cwd.encode()).hexdigest()}.json")

    if should_restart:
        if os.path.exists(history_file): os.remove(history_file)
        print(f"\033[92m[✓] Sesión reiniciada para: {path_key}\033[0m")
        if not clean_args: sys.exit(0)

    try:
        client = genai.Client(api_key=api_key)
        history = load_history(history_file)
        
        print(f"\033[90m[Sesión: {path_key}] [{len(history)} msgs]\033[0m")

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
                if user_input.startswith("/help"): show_help(); continue
                if user_input.startswith("/restart"):
                    if os.path.exists(history_file): os.remove(history_file)
                    chat = client.chats.create(model=MODEL_NAME, history=[], config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT))
                    print("\033[92mSesión limpia.\033[0m"); continue
                
                res = chat.send_message(user_input)
                clean_res = clean_markdown(res.text)
                print("\n" + clean_res + "\n")
                save_history(chat, history_file)
        else:
            res = chat.send_message(prompt)
            clean_res = clean_markdown(res.text)
            print("\n" + clean_res + "\n")
            save_history(chat, history_file)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
