import os
import sys
import json
import hashlib
import socket
import requests
import argparse
from google import genai
from google.genai import types

# Configuración de Modelos
GEMINI_MODEL = "gemini-3.1-flash-lite-preview"
OLLAMA_MODEL = "qwen2.5:1.5b"
OLLAMA_URL = "http://100.115.152.45:11434/api/generate" # IP de Iqual-Mint en Tailscale

def ask_gemini(prompt, api_key):
    try:
        client = genai.Client(api_key=api_key)
        # Contexto mínimo para ahorrar tokens
        sys_p = f"Eres Gemini 3.1 en {socket.gethostname()}. Responde directo y código puro."
        res = client.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=types.GenerateContentConfig(system_instruction=sys_p))
        return res.text
    except Exception as e:
        raise e

def ask_ollama(prompt):
    try:
        res = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}, timeout=60)
        return res.json().get('response', 'Error en IA Local')
    except Exception as e:
        return f"\033[91m[!] IA Local no disponible (Iqual-Mint Offline): {e}\033[0m"

def main():
    parser = argparse.ArgumentParser(description="Selector de IA Personal de Jorge (2026)", add_help=False)
    parser.add_argument("-l", "--local", action="store_true", help="Forzar IA Local (Qwen 3B)")
    parser.add_argument("-g", "--gemini", action="store_true", help="Forzar Gemini 3.1 (Nube)")
    parser.add_argument("-h", "--help", action="store_true", help="Mostrar esta ayuda")
    parser.add_argument("message", nargs="*", help="Tu mensaje para la IA")
    
    args = parser.parse_args()

    if args.help:
        print("\033[94m--- PANEL DE IA JORGE 2026 ---\033[0m")
        print("Uso: chat [opciones] [mensaje]")
        print("  (sin flags)  -> Modo Auto (Gemini con fallback a Local)")
        print("  -l, --local  -> IA Local (Qwen 3B en Iqual-Mint)")
        print("  -g, --gemini -> IA Nube (Gemini 3.1 sin fallback)")
        print("  -h, --help   -> Mostrar este menú")
        return

    prompt = " ".join(args.message)
    if not prompt.strip():
        print("\033[93m[!] Por favor, escribe un mensaje.\033[0m")
        return

    api_key = os.environ.get("GEMINI_API_KEY")

    # LÓGICA DE RUTEO
    if args.local:
        print("\033[90m[Modo: Forzar Local (Qwen 3B)]\033[0m")
        print(ask_ollama(prompt))
    
    elif args.gemini:
        print("\033[90m[Modo: Forzar Nube (Gemini 3.1)]\033[0m")
        try:
            print(ask_gemini(prompt, api_key))
        except Exception as e:
            print(f"\033[91m[Error Gemini]: {e}\033[0m")
    
    else:
        # MODO AUTOMÁTICO (Default)
        try:
            # Intento Gemini
            print(ask_gemini(prompt, api_key))
        except Exception as e:
            if any(err in str(e) for err in ["402", "429", "quota", "Quota"]):
                print("\033[93m[FALLBACK] Cuota de Google agotada. Saltando a IA Local en Iqual-Mint...\033[0m")
                print(ask_ollama(prompt))
            else:
                print(f"\033[91m[Error crítico]: {e}\033[0m")

if __name__ == "__main__":
    main()
