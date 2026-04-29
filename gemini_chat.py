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
CEREBRAS_MODEL = "qwen2.5-72b"
SAMBANOVA_MODEL = "Meta-Llama-3.1-70B-Instruct"
MISTRAL_MODEL = "mistral-tiny"

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

def ask_openai_style(url, model, api_key, prompt, history, provider_name):
    messages = [{"role": "system", "content": get_system_prompt()}] + history + [{"role": "user", "content": prompt}]
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "stream": False}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        res.raise_for_status()
        return res.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"\033[90m[Fallback] {provider_name} falló: {e}\033[0m")
        return None

def ask_gemini(prompt, api_key, history):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"
    contents = [{"role": "user" if m["role"]=="user" else "model", "parts": [{"text": m["content"]}]} for m in history]
    contents.append({"role": "user", "parts": [{"text": f"{get_system_prompt()}\n\n{prompt}"}]})
    res = requests.post(url, json={"contents": contents}, timeout=10)
    res.raise_for_status()
    return res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

def ask_ollama(prompt, history):
    url = "http://100.115.152.45:11434/api/chat"
    messages = [{"role": "system", "content": get_system_prompt()}] + history + [{"role": "user", "content": prompt}]
    res = requests.post(url, json={"model": "qwen2.5:1.5b", "messages": messages, "stream": False}, timeout=10)
    res.raise_for_status()
    return res.json().get('message', {}).get('content', 'Error')

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-r", "--restart", action="store_true")
    parser.add_argument("message", nargs="*")
    args = parser.parse_args()

    prompt = " ".join(args.message)
    if not prompt.strip(): return

    h_file = get_h_file(False)
    if args.restart and os.path.exists(h_file): os.remove(h_file)

    history = load_history(h_file)
    keys = {
        "gemini": os.environ.get("GEMINI_API_KEY"),
        "cerebras": "REMOVED",
        "sambanova": "REMOVED",
        "mistral": "REMOVED"
    }

    print(f"\033[90m[AUTO] [{socket.gethostname().upper()}] [H:{len(history)//2}]\033[0m")

    res_text = None
    # CADENA DE FALLBACK INDESTRUCTIBLE
    # 1. Gemini
    try:
        res_text = ask_gemini(prompt, keys["gemini"], history)
        if res_text: print(f"\033[32m[GEMINI]\033[0m {clean_terminal_output(res_text)}"); goto_save = True
    except:
        # 2. Cerebras
        res_text = ask_openai_style("https://api.cerebras.ai/v1/chat/completions", CEREBRAS_MODEL, keys["cerebras"], prompt, history, "Cerebras")
        if res_text: print(f"\033[33m[CEREBRAS]\033[0m {clean_terminal_output(res_text)}"); goto_save = True
        else:
            # 3. SambaNova
            res_text = ask_openai_style("https://api.sambanova.ai/v1/chat/completions", SAMBANOVA_MODEL, keys["sambanova"], prompt, history, "SambaNova")
            if res_text: print(f"\033[34m[SAMBANOVA]\033[0m {clean_terminal_output(res_text)}"); goto_save = True
            else:
                # 4. Mistral
                res_text = ask_openai_style("https://api.mistral.ai/v1/chat/completions", MISTRAL_MODEL, keys["mistral"], prompt, history, "Mistral")
                if res_text: print(f"\033[35m[MISTRAL]\033[0m {clean_terminal_output(res_text)}"); goto_save = True
                else:
                    # 5. Local (Ollama)
                    try:
                        res_text = ask_ollama(prompt, history)
                        print(f"\033[36m[LOCAL]\033[0m {clean_terminal_output(res_text)}"); goto_save = True
                    except Exception as e:
                        print(f"\033[91m[!] Error Crítico: Todos los proveedores fallaron.\033[0m")
                        return

    if res_text:
        save_history(h_file, history, prompt, clean_terminal_output(res_text))

if __name__ == "__main__":
    main()
