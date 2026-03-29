import os
import sys
import json
import hashlib
import socket
import requests
import argparse
import platform
import re
from datetime import datetime
from google import genai
from google.genai import types

# ==================================================================================
# ⚠️ LLM MANDATE / CONTRATO DE DESARROLLO (2026) ⚠️
# ----------------------------------------------------------------------------------
# 1. PRESERVAR FUNCIONES: Memoria, Selector IA, Fallback, Contexto, Stream.
# 2. AUTO-EXPANSIÓN: Si agregas una función, DEBES añadirla a esta lista.
# 3. ROBUSTEZ: Prohibido colgarse por red. Usar timeouts (5s conn, 90s read).
# 4. TESTING: Antes de guardar, ejecutar: python3 test_chat_logic.py
# 5. PUREZA DE TERMINAL: Salida en texto plano, sin markdown ni símbolos raros.
# ==================================================================================

GEMINI_MODEL = "gemini-3.1-flash-lite-preview"
OLLAMA_MODEL = "qwen2.5:1.5b"
OLLAMA_URL = "http://100.115.152.45:11434/api/chat"

PROMPTS = {
    "jorge-thinkpad-x270": "NODO MAESTRO. Estación de desarrollo principal.",
    "raspberrypi": "NODO MULTIMEDIA. Control de hardware y domótica.",
    "iqual-mint": "NODO SERVIDOR. Almacenamiento y servicios backend."
}

def clean_terminal_output(text):
    if not text: return ""
    text = re.sub(r'```[a-zA-Z0-9_-]*\s*\n', '', text)
    text = re.sub(r'```', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    text = re.sub(r'^#+\s+', '', text, flags=re.M)
    return text.strip()

def get_system_prompt():
    host = socket.gethostname().lower()
    dev_context = PROMPTS.get(host, "Asistente Linux.")
    return (f"CONTEXTO: {dev_context} | HOST: {host.upper()} | AÑO: {datetime.now().year}. "
            f"REGLA: Responde en TEXTO PLANO. PROHIBIDO: Markdown, negritas o bloques ```.")

def get_h_file(is_global):
    h_dir = os.path.expanduser("~/.gemini_chat/sessions")
    os.makedirs(h_dir, exist_ok=True)
    if is_global: return os.path.join(h_dir, "global.json")
    return os.path.join(h_dir, f"{hashlib.md5(os.getcwd().encode()).hexdigest()}.json")

def load_history(h_file):
    if os.path.exists(h_file):
        try:
            with open(h_file, "r") as f: return json.load(f)
        except: return []
    return []

def save_history(h_file, history, user_msg, model_res):
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": model_res})
    with open(h_file, "w") as f: json.dump(history[-20:], f)

def ask_gemini(prompt, api_key, history, stream=True):
    client = genai.Client(api_key=api_key)
    h_objs = [types.Content(role=("user" if m["role"]=="user" else "model"), 
              parts=[types.Part(text=m["content"])]) for m in history]
    full_res = ""
    config = types.GenerateContentConfig(system_instruction=get_system_prompt(), history=h_objs)
    if stream:
        for chunk in client.models.generate_content_stream(model=GEMINI_MODEL, contents=prompt, config=config):
            text = chunk.text or ""
            print(text, end="", flush=True); full_res += text
        print()
    else:
        res = client.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=config)
        full_res = res.text; print(clean_terminal_output(full_res))
    return full_res

def ask_ollama(prompt, history, stream=True):
    messages = [{"role": "system", "content": get_system_prompt()}] + history + [{"role": "user", "content": prompt}]
    try:
        res = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "messages": messages, "stream": stream}, 
                            timeout=(5, 180), stream=stream)
        res.raise_for_status()
        full_res = ""
        if stream:
            for line in res.iter_lines():
                if line:
                    chunk = json.loads(line)
                    content = chunk.get('message', {}).get('content', '')
                    print(content, end="", flush=True); full_res += content
            print()
        else:
            full_res = res.json().get('message', {}).get('content', 'Error')
            print(clean_terminal_output(full_res))
        return full_res
    except Exception as e:
        err_msg = f"\033[91m[!] Error de red: {e}\033[0m"
        print(err_msg)
        return err_msg

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-l", "--local", action="store_true")
    parser.add_argument("-g", "--global-mode", action="store_true")
    parser.add_argument("-s", "--stream", action="store_true", default=True)
    parser.add_argument("-ns", "--no-stream", action="store_false", dest="stream")
    parser.add_argument("-r", "--restart", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("message", nargs="*")
    args = parser.parse_args()

    if args.help:
        print("\033[94mChat Terminal 2026\033[0m: chat [-l local] [-g global] [-r restart] 'mensaje'"); return

    prompt = " ".join(args.message)
    if not prompt.strip(): return

    h_file = get_h_file(args.global_mode)
    if args.restart and os.path.exists(h_file):
        os.remove(h_file); print("\033[90m[Sesión reiniciada]\033[0m")

    history = load_history(h_file)
    api_key = os.environ.get("GEMINI_API_KEY")

    mode_label = "LOCAL" if args.local else "NUBE"
    print(f"\033[90m[{mode_label}] [{socket.gethostname().upper()}] [H:{len(history)//2}] [Reset: -r]\033[0m")

    try:
        if args.local:
            res_text = ask_ollama(prompt, history, stream=args.stream)
        else:
            try:
                res_text = ask_gemini(prompt, api_key, history, stream=args.stream)
            except Exception as e:
                if any(err in str(e) for err in ["402", "429", "quota"]):
                    print("\033[93m[FALLBACK] Saltando a Local...\033[0m")
                    res_text = ask_ollama(prompt, history, stream=args.stream)
                else: 
                    print(f"\033[91m[Error Gemini]: {e}\033[0m")
                    return
        
        if res_text and not res_text.startswith("\033[91m"):
            save_history(h_file, history, prompt, clean_terminal_output(res_text))
    except Exception as e: print(f"Error Crítico: {e}")

if __name__ == "__main__":
    main()
