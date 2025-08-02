# Contenido de: ~/bot_telegram/ask_gemini.py

import google.generativeai as genai
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Configura la API key desde la variable de entorno
try:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise KeyError
    genai.configure(api_key=api_key)
except KeyError:
    print("Error: La variable de entorno GEMINI_API_KEY no está configurada o está vacía.", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Error al configurar la API de Gemini: {e}", file=sys.stderr)
    sys.exit(1)

# Configuración del modelo
generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model = genai.GenerativeModel(
    model_name= "gemini-2.5-flash", #"gemini-2.0-flash"  #"gemini-1.5-flash-latest", # O el modelo que prefieras y tengas acceso
    generation_config=generation_config,
    safety_settings=safety_settings
)

def preguntar_a_gemini(pregunta):
    """Envía la pregunta a Gemini y devuelve la respuesta."""
    try:
        config = "Te hablo desde una terminal de un server linux LocOS muy limitado, Intel Atom N270 (2) @ 1.60,  de 32 bit y 1 de ram," /
         ", se trata de ser breve, pero si es necesario extiendete un poco. Utiliza formas y dibujos en codigo ascii para que sea mas llevadero." /
         "consulta:\n"
        prompt = config + pregunta
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error al contactar a Gemini: {e}", file=sys.stderr)
        # Podrías querer devolver un mensaje de error específico o simplemente dejar que el sys.exit(1) ocurra
        # Por ahora, imprimimos a stderr y el script principal (bot) manejará la salida vacía o el error.
        return None # Opcional: podrías hacer sys.exit(1) aquí también.

if __name__ == "__main__":
    # Modo para Telegram: espera la pregunta como argumentos después de --telegram-mode
    if "--telegram-mode" in sys.argv:
        try:
            pregunta_index = sys.argv.index("--telegram-mode") + 1
            if len(sys.argv) > pregunta_index:
                pregunta_usuario = " ".join(sys.argv[pregunta_index:])
                if not pregunta_usuario.strip():
                    print("Error: Pregunta vacía en modo telegram.", file=sys.stderr)
                    sys.exit(1)
                respuesta = preguntar_a_gemini(pregunta_usuario)
                if respuesta:
                    print(respuesta) # Solo imprime la respuesta directa para el bot
                    sys.exit(0) # Salida exitosa
                else:
                    # preguntar_a_gemini ya imprimió el error a stderr
                    print("No se obtuvo respuesta de Gemini.", file=sys.stderr) # Mensaje adicional
                    sys.exit(1) # Salida con error
            else:
                print("Error: No se proporcionó pregunta después de --telegram-mode.", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            print(f"Error interno en modo telegram: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Modo interactivo/directo para la terminal (opcional, puedes quitarlo si solo es para el bot)
    elif len(sys.argv) > 1:
        pregunta_usuario = " ".join(sys.argv[1:])
        respuesta = preguntar_a_gemini(pregunta_usuario)
        if respuesta:
            print("\n")
            print(respuesta)
            sys.exit(0)
        else:
            # preguntar_a_gemini ya imprimió el error a stderr
            sys.exit(1)
    else:
        print("Uso para bot: python ask_gemini.py --telegram-mode <tu pregunta aquí>", file=sys.stderr)
        print("Uso para terminal: python ask_gemini.py <tu pregunta aquí>", file=sys.stderr)
        sys.exit(1)
