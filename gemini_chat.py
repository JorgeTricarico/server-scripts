import os
import sys
from google import genai

# Configuración del modelo (Marzo 2026)
# Usamos gemini-2.0-flash como fallback seguro si gemini-3-flash-preview no responde
MODEL_NAME = "gemini-3-flash-preview"

def main():
    # Obtener API Key de la variable de entorno
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("\033[91mError: La variable de entorno GEMINI_API_KEY no está configurada.\033[0m")
        sys.exit(1)

    try:
        # Nueva forma de inicializar el cliente en google-genai
        client = genai.Client(api_key=api_key)
        
        # Leer pregunta de los argumentos
        if len(sys.argv) > 1:
            prompt = " ".join(sys.argv[1:])
        else:
            print(f"\033[94m-- Modo Interactivo (Gemini Series 3) --\033[0m")
            print("Escribe tu pregunta (o 'salir' para terminar):")
            try:
                prompt = input("> ")
                if prompt.lower() in ["salir", "exit", "quit"]:
                    return
            except EOFError:
                return

        if not prompt.strip():
            return

        # Generar contenido con el nuevo SDK
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        
        print("\n" + response.text + "\n")
        
    except Exception as e:
        print(f"\033[91mError al contactar a Gemini: {e}\033[0m")
        sys.exit(1)

if __name__ == "__main__":
    main()
