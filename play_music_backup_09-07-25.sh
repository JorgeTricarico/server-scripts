#!/bin/bash

# play_music.sh - Reproduce música de YouTube, descargándola si no existe localmente.

# Añadir el directorio donde está yt-dlp a PATH.
# ASEGÚRATE DE USAR LA LÍNEA CORRECTA PARA TU INSTALACIÓN DE YT-DLP:
# Si lo instalaste con pip en ~/.local/bin:
export PATH="$HOME/.local/bin:$PATH"
# O, si está en un entorno virtual como en tu backup:
# export PATH="$HOME/yt-env/bin:$PATH" # <--- DESCOMENTA Y USA ESTA SI ES TU CASO

# Directorio de descarga y almacenamiento de música.
# ASEGÚRATE DE CAMBIAR ESTA RUTA A LA DE TU DISCO EXTERNO.
DOWNLOAD_DIR="$HOME/disco_externo/music"

# Asegurarse de que el directorio de descarga exista
mkdir -p "$DOWNLOAD_DIR"

# Función para limpiar el título para usarlo como nombre de archivo
# Elimina caracteres especiales, reemplaza espacios con guiones bajos, etc.
sanitize_filename() {
    local filename="$1"
    # Reemplaza espacios con guiones bajos
    filename="${filename// /_}"
    # Convierte a minúsculas
    filename="${filename,,}"
    # Elimina caracteres no alfanuméricos excepto guiones, puntos y barra (para extensiones)
    # Importante: Si yt-dlp añade números al final para desambiguar, la sanitización solo se aplica al título original.
    filename=$(echo "$filename" | sed 's/[^a-z0-9_.-]//g')
    # Elimina guiones bajos duplicados o guiones al inicio/fin
    filename=$(echo "$filename" | sed 's/__*/_/g' | sed 's/^_//;s/_$//')
    # Elimina puntos duplicados o puntos al inicio/fin
    filename=$(echo "$filename" | sed 's/\.\.+/./g' | sed 's/^\.//;s/\.$//')
    echo "$filename"
}


# --- Mostrar el volumen actual al inicio ---
echo "" # Línea en blanco para mejor legibilidad
# Llama al script set_volume.sh para que muestre el volumen actual.
# Se asume que set_volume.sh está en el mismo directorio o en el PATH.
~/scripts/set_volume.sh
echo "" # Línea en blanco para mejor legibilidad


# Verificar si se proporcionó un término de búsqueda
if [ -z "$1" ]; then
    echo "Uso: $0 <término de búsqueda>"
    exit 1
fi

SEARCH_TERM="$*" # Captura todos los argumentos como término de búsqueda

echo "Buscando en YouTube: $SEARCH_TERM"

# --- Obtener Metadata (Título, URL, Duración) ---
# Usamos --print-json para obtener todos los detalles y jq para parsearlos.
# 2>/dev/null para suprimir advertencias de yt-dlp
METADATA=$(yt-dlp --dump-json --default-search "ytsearch" "$SEARCH_TERM" 2>/dev/null | head -n 1)

# Verificar si se obtuvo alguna metadata
if [ -z "$METADATA" ]; then
    echo "No se encontraron resultados para '$SEARCH_TERM'."
    exit 1
fi

# Extraer el título, URL y duración del JSON
VIDEO_TITLE=$(echo "$METADATA" | jq -r '.title')
VIDEO_URL=$(echo "$METADATA" | jq -r '.webpage_url')
DURATION_SECONDS=$(echo "$METADATA" | jq -r '.duration')

# Formatear la duración (ej: 3600 segundos -> 01:00:00)
format_duration() {
    local seconds=$1
    if [ -z "$seconds" ] || [ "$seconds" = "null" ]; then
        echo "Desconocida"
        return
    fi
    local hours=$((seconds / 3600))
    local minutes=$(( (seconds % 3600) / 60 ))
    local remaining_seconds=$((seconds % 60))
    printf "%02d:%02d:%02d" "$hours" "$minutes" "$remaining_seconds"
}

FORMATTED_DURATION=$(format_duration "$DURATION_SECONDS")

echo "Título encontrado: $VIDEO_TITLE"
echo "URL: $VIDEO_URL"
echo "Duración: $FORMATTED_DURATION"

# --- Determinar el nombre de archivo MP3 esperado (AHORA LOCALMENTE CON SANITIZACIÓN) ---
# Usamos la función sanitize_filename para crear un nombre de archivo seguro
BASE_FILENAME_SANITIZED=$(sanitize_filename "$VIDEO_TITLE")
EXPECTED_AUDIO_FILE="$DOWNLOAD_DIR/${BASE_FILENAME_SANITIZED}.mp3"
AUIDO_FILE="${BASE_FILENAME_SANITIZED}.mp3"

# --- Lógica de Descarga y Reproducción ---
if [ -f "$EXPECTED_AUDIO_FILE" ]; then
    echo "El archivo ya existe!"
    echo "Reproduciendo: $AUDIO_FILE"
    mpv --no-video "$EXPECTED_AUDIO_FILE" >/dev/null 2>&1 &
    MPV_PID=$!
    echo "mpv iniciado en segundo plano con PID: $MPV_PID"
    echo "Para detener: kill $MPV_PID"
    echo "$MPV_PID" > /tmp/mpv_music.pid
else
    echo "El archivo no existe." 
    echo "Descargando: $VIDEO_TITLE"

    # Descargar el archivo de audio como MP3
    # AHORA: Intentamos priorizar la descarga de formatos de audio puro (m4a, webm)
    # y luego convertir a mp3. --no-keep-video asegura que se borren los temporales.
    # El orden de -f es importante: bestaudio[ext=m4a] primero, luego bestaudio[ext=webm], luego bestaudio general.
    if yt-dlp -f "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio" --extract-audio --audio-format mp3 --audio-quality 0 --restrict-filenames --no-keep-video -o "$EXPECTED_AUDIO_FILE" "$VIDEO_URL" >/dev/null 2>&1; then
        echo "Descarga completa."

        if [ -f "$EXPECTED_AUDIO_FILE" ]; then
            echo "Reproduciendo: $AUDIO_FILE"
            mpv --no-video "$EXPECTED_AUDIO_FILE" >/dev/null 2>&1 &
            MPV_PID=$!
            echo "mpv iniciado en segundo plano con PID: $MPV_PID"
            echo "Para detener: kill $MPV_PID"
            echo "$MPV_PID" > /tmp/mpv_music.pid
        else
            echo "Error: El archivo descargado no se encontró en la ruta esperada: $EXPECTED_AUDIO_FILE"
            echo "Intentando reproducir en streaming como fallback."
            mpv --no-video "$VIDEO_URL" >/dev/null 2>&1 & # Fallback a streaming
            MPV_PID=$!
            echo "mpv (streaming) iniciado en segundo plano con PID: $MPV_PID"
            echo "Para detener: kill $MPV_PID"
            echo "$MPV_PID" > /tmp/mpv_music.pid
        fi
    else
        echo "Error al descargar el video. Intentando reproducir en streaming."
        mpv --no-video "$VIDEO_URL" >/dev/null 2>&1 &
        MPV_PID=$!
        echo "mpv (streaming) iniciado en segundo plano con PID: $MPV_PID"
        echo "Para detener: kill $MPV_PID"
        echo "$MPV_PID" > /tmp/mpv_music.pid
    fi
fi
