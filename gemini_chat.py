import os
import sys
import json
import hashlib
import socket
import requests
import argparse
import re
from datetime import datetime

# Intentar cargar .env si existe
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
except ImportError:
    pass

# CONFIGURACIÓN DE MODELOS
GEMINI_MODEL = "gemini-3.1-flash-lite-preview"
CEREBRAS_MODEL = "qwen2.5-72b"
SAMBANOVA_MODEL = "Meta-Llama-3.1-70B-Instruct"
MISTRAL_MODEL = "mistral-tiny"

def clean_terminal_output(text):
    if not text: return ""
    text = re.sub(r'```[a-zA-Z0-9_-]*\s*\n', '', text)
    text = re.sub(r'```', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    return text.strip()

def get_system_prompt():
    host = socket.gethostname().upper()
    return f"Responde en TEXTO PLANO (sin markdown). Host: {host}. Año: 2026."

def get_h_file():
    h_dir = os.path.expanduser("~/.gemini_chat/sessions")
    os.makedirs(h_dir, exist_ok=True)
    return os.path.join(h_dir, "global.json")

def ask_openai_style(url, model, api_key, prompt, history):
    if not api_key: return None
    messages = [{"role": "system", "content": get_system_prompt()}] + history + [{"role": "user", "content": prompt}]
    try:
        res = requests.post(url, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, 
                            json={"model": model, "messages": messages, "stream": False}, timeout=10)
        if res.ok: return res.json()['choices'][0]['message']['content'].strip()
    except: return None
    return None

def ask_gemini(prompt, api_key, history):
    if not api_key: return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"
    contents = [{"role": "user" if m["role"]=="user" else "model", "parts": [{"text": m["content"]}]} for m in history]
    contents.append({"role": "user", "parts": [{"text": f"{get_system_prompt()}\n\n{prompt}"}]})
    try:
        res = requests.post(url, json={"contents": contents}, timeout=10)
        if res.ok: return res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except: pass
    return None

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-r", "--restart", action="store_true")
    parser.add_argument("message", nargs="*")
    args = parser.parse_args()

    prompt = " ".join(args.message)
    if not prompt.strip(): return

    h_file = get_h_file()
    if args.restart and os.path.exists(h_file): os.remove(h_file)

    history = []
    if os.path.exists(h_file):
        try:
            with open(h_file, "r") as f: history = json.load(f)
        except: pass

    # CARGAR LLAVES DESDE EL ENTORNO
    keys = {
        "gemini": os.environ.get("GEMINI_API_KEY"),
        "cerebras": os.environ.get("CEREBRAS_API_KEY"),
        "sambanova": os.environ.get("SAMBANOVA_API_KEY"),
        "mistral": os.environ.get("MISTRAL_API_KEY")
    }

    res_text = None
    # CADENA SILENCIOSA
    res_text = ask_gemini(prompt, keys["gemini"], history)
    if res_text: label = "GEMINI"
    else:
        res_text = ask_openai_style("https://api.cerebras.ai/v1/chat/completions", CEREBRAS_MODEL, keys["cerebras"], prompt, history)
        if res_text: label = "CEREBRAS"
        else:
            res_text = ask_openai_style("https://api.sambanova.ai/v1/chat/completions", SAMBANOVA_MODEL, keys["sambanova"], prompt, history)
            if res_text: label = "SAMBANOVA"
            else:
                res_text = ask_openai_style("https://api.mistral.ai/v1/chat/completions", MISTRAL_MODEL, keys["mistral"], prompt, history)
                if res_text: label = "MISTRAL"

    if res_text:
        clean_res = clean_terminal_output(res_text)
        print(f"[{label}] {clean_res}")
        history.append({"role": "user", "content": prompt})
        history.append({"role": "assistant", "content": clean_res})
        with open(h_file, "w") as f: json.dump(history[-10:], f)
    else:
        print("\033[91m[!] Sin conexión con IAs (Verifica tus llaves en .env)\033[0m")

if __name__ == "__main__":
    main()
