import os
import sys
import json
import hashlib
import socket
import platform
import re
from datetime import datetime
from google import genai
from google.genai import types

MODEL_NAME = "gemini-3.1-flash-lite-preview"

def get_context():
    now = datetime.now()
    return {
        "year": now.year,
        "date": now.strftime("%d/%m/%Y %H:%M:%S"),
        "os": platform.platform(),
        "node": socket.gethostname().upper()
    }

def show_help():
    print("""
\033[94mGemini Chat CLI 2026\033[0m
Uso: \033[93mchat [opciones] [mensaje]\033[0m
  -h, --help     Ayuda
  -r, --restart  Reiniciar sesión
  -g, --global   Sesión global
""")

def clean_md(text):
    return re.sub(r'```[a-zA-Z0-9_-]*\s*\n|```', '', text)

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return

    args = sys.argv[1:]
    if "-h" in args or "--help" in args:
        show_help(); sys.exit(0)

    is_global = "-g" in args or "--global" in args
    should_restart = "-r" in args or "--restart" in args
    msg_args = [a for a in args if a not in ["-g", "--global", "-r", "--restart"]]
    
    ctx = get_context()
    h_file = os.path.expanduser("~/.gemini_chat/sessions/" + ("global.json" if is_global else f"{hashlib.md5(os.getcwd().encode()).hexdigest()}.json"))
    os.makedirs(os.path.dirname(h_file), exist_ok=True)

    if should_restart and os.path.exists(h_file): os.remove(h_file)

    raw_h = []
    if os.path.exists(h_file):
        try:
            with open(h_file, "r") as f: raw_h = json.load(f)
        except: raw_h = []
    
    # CORRECCIÓN DE SINTAXIS AQUÍ:
    h_objs = []
    for m in raw_h:
        h_objs.append(types.Content(role=m["role"], parts=[types.Part(text=m["text"])]))

    try:
        client = genai.Client(api_key=api_key)
        sys_p = f"Asistente en {ctx['node']} ({ctx['year']}). REGLA: Responde DIRECTO, sin markdown, código puro."
        chat = client.chats.create(model=MODEL_NAME, history=h_objs, config=types.GenerateContentConfig(system_instruction=sys_p))

        prompt = " ".join(msg_args)
        if not prompt.strip():
            print(f"[{ctx['node']}] [H:{len(raw_h)}]")
            while True:
                try: user_input = input("> ")
                except: break
                if user_input.lower() in ["exit", "quit"]: break
                res = chat.send_message(user_input)
                print("\n" + clean_md(res.text) + "\n")
                raw_h.append({"role": "user", "text": user_input})
                raw_h.append({"role": "model", "text": res.text})
                with open(h_file, "w") as f: json.dump(raw_h[-20:], f)
        else:
            res = chat.send_message(prompt)
            print(clean_md(res.text))
            raw_h.append({"role": "user", "text": prompt})
            raw_h.append({"role": "model", "text": res.text})
            with open(h_file, "w") as f: json.dump(raw_h[-20:], f)
    except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    main()
