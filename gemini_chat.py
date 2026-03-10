import os
import sys
from google import genai

# Configuración del modelo y directivas estrictas para terminal de servidor
MODEL_NAME = "gemini-3.1-flash-lite-preview"

SYSTEM_PROMPT = (
    "Eres mi colega Senior de programación y administrador de sistemas. "
    "REGLA CRÍTICA: Estás respondiendo en una terminal remota/servidor. "
    "Tus respuestas DEBEN ser extremadamente concisas, directas y al grano. "
    "NUNCA des introducciones, saludos, ni conclusiones largas. "
    "Muestra el comando o la configuración solicitada directamente, seguido de "
    "una breve explicación técnica de 1 a 2 líneas si es necesario. "
    "No uses ASCII art que consuma espacio en la consola."
)

def main():
    # Obtener API Key de la variable de entorno
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("\033[91mError: La variable de entorno GEMINI_API_KEY no está configurada.\033[0m")
        sys.exit(1)

    try:
        client = genai.Client(api_key=api_key)
        
        # Leer pregunta de los argumentos
        if len(sys.argv) > 1:
            prompt = " ".join(sys.argv[1:])
        else:
            print(f"\033[94m-- Modo Servidor / Terminal (Gemini Series 3.1) --\033[0m")
            print("Consulta (o 'salir' para terminar):")
            try:
                prompt = input("> ")
                if prompt.lower() in ["salir", "exit", "quit"]:
                    return
            except EOFError:
                return

        if not prompt.strip():
            return

        # Generar contenido con contexto de sistema
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[SYSTEM_PROMPT, prompt]
        )
        
        if response.text:
            print("\n" + response.text + "\n")
        else:
            print("\033[93mEl modelo no devolvió texto.\033[0m")
        
    except Exception as e:
        print(f"\033[91mError al contactar a Gemini: {e}\033[0m")
        sys.exit(1)

if __name__ == "__main__":
    main()
