#!/bin/bash

# play_music.sh - Reproduce música de YouTube, descargándola si no existe localmente.
# Versión con caché de prompts.

# --- CONFIGURACIÓN ---
# Directorio de descarga y almacenamiento de música.
DOWNLOAD_DIR="$HOME/disco_externo/music"
# Archivo para mapear prompts a rutas de canciones.
PROMPT_MAP_FILE="$DOWNLOAD_DIR/prompt_song_map.txt"

# Asegurarse de que el directorio de descarga y el archivo de mapa existan
mkdir -p "$DOWNLOAD_DIR"
touch "$PROMPT_MAP_FILE"

# Añadir yt-dlp al PATH
export PATH="$HOME/.local/bin:$PATH"

# --- FUNCIONES ---

# Limpia un string para usarlo como nombre de archivo.
sanitize_filename() {
    local filename="$1"
    filename="${filename// /_}"
    filename="${filename,,}"
    filename=$(echo "$filename" | sed 's/[^a-z0-9_.-]//g')
    filename=$(echo "$filename" | sed 's/__*/_/g' | sed 's/^_//;s/_$//')
    filename=$(echo "$filename" | sed 's/\.\.+/./g' | sed 's/^\.//;s/\.$//')
    echo "$filename"
}

# Formatea la duración en segundos a HH:MM:SS.
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

# Reproduce una canción y guarda el PID.
play_song() {
    local file_path="$1"
    local song_name
    song_name=$(basename "$file_path")
    echo "Reproduciendo: $song_name"
    mpv --no-video "$file_path" >/dev/null 2>&1 &
    MPV_PID=$!
    echo "mpv iniciado en segundo plano con PID: $MPV_PID"
    echo "Para detener: kill $MPV_PID"
    echo "$MPV_PID" > /tmp/mpv_music.pid
}

# --- SCRIPT PRINCIPAL ---

# Mostrar el volumen actual
echo ""
~/scripts/set_volume.sh
echo ""

# Verificar si se proporcionó un término de búsqueda
if [ -z "$1" ]; then
    echo "Uso: $0 <término de búsqueda>"
    exit 1
fi

SEARCH_TERM="$*" # Captura todos los argumentos como término de búsqueda

# 1. BÚSQUEDA EN CACHÉ DE PROMPTS
# Buscamos el prompt exacto en nuestro archivo de mapeo.
# Usamos `grep -F` para búsqueda de string literal y ` -m 1` para detenernos en la primera coincidencia.
# `cut -d ':' -f 4-` maneja prompts que puedan contener ':::'
MATCHING_SONG_PATH=$(grep -Fm 1 "$SEARCH_TERM ::: " "$PROMPT_MAP_FILE" | cut -d ':' -f 4- | sed 's/^ *//;s/ *$//') # sed para quitar espacios extra

if [ -n "$MATCHING_SONG_PATH" ] && [ -f "$MATCHING_SONG_PATH" ]; then
    echo "Prompt encontrado en caché!"
    play_song "$MATCHING_SONG_PATH"
    exit 0
fi

# Si no está en caché, continuamos con la búsqueda en YouTube.
echo "Buscando en YouTube: $SEARCH_TERM"

# 2. OBTENER METADATA DE YOUTUBE
METADATA=$(yt-dlp --dump-json --default-search "ytsearch" "$SEARCH_TERM" 2>/dev/null | head -n 1)

if [ -z "$METADATA" ]; then
    echo "No se encontraron resultados para '$SEARCH_TERM'."
    exit 1
fi

VIDEO_TITLE=$(echo "$METADATA" | jq -r '.title')
VIDEO_URL=$(echo "$METADATA" | jq -r '.webpage_url')
DURATION_SECONDS=$(echo "$METADATA" | jq -r '.duration')
FORMATTED_DURATION=$(format_duration "$DURATION_SECONDS")

echo "Título encontrado: $VIDEO_TITLE"
echo "URL: $VIDEO_URL"
echo "Duración: $FORMATTED_DURATION"

# 3. DETERMINAR NOMBRE DE ARCHIVO Y VERIFICAR EXISTENCIA
BASE_FILENAME_SANITIZED=$(sanitize_filename "$VIDEO_TITLE")
EXPECTED_AUDIO_FILE="$DOWNLOAD_DIR/${BASE_FILENAME_SANITIZED}.mp3"

# 4. LÓGICA DE DESCARGA Y REPRODUCCIÓN
if [ -f "$EXPECTED_AUDIO_FILE" ]; then
    echo "El archivo ya existe!"
    play_song "$EXPECTED_AUDIO_FILE"
else
    echo "El archivo no existe. Descargando..."
    if yt-dlp -f "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio" --extract-audio --audio-format mp3 --audio-quality 0 --restrict-filenames --no-keep-video -o "$EXPECTED_AUDIO_FILE" "$VIDEO_URL" >/dev/null 2>&1; then
        echo "Descarga completa."
        if [ -f "$EXPECTED_AUDIO_FILE" ]; then
            play_song "$EXPECTED_AUDIO_FILE"
        else
            echo "Error: El archivo descargado no se encontró. Intentando streaming como fallback."
            play_song "$VIDEO_URL" # Fallback a streaming
        fi
    else
        echo "Error al descargar. Intentando streaming como fallback."
        play_song "$VIDEO_URL" # Fallback a streaming
    fi
fi

# 5. GUARDAR EN CACHÉ (SI LA CANCIÓN SE REPRODUJO LOCALMENTE)
# Solo guardamos la relación si el archivo existe en el disco.
if [ -f "$EXPECTED_AUDIO_FILE" ]; then
    # Verificamos que el prompt no exista ya para evitar duplicados.
    if ! grep -Fq "$SEARCH_TERM ::: $EXPECTED_AUDIO_FILE" "$PROMPT_MAP_FILE"; then
        echo "Guardando nuevo prompt en caché..."
        echo "$SEARCH_TERM ::: $EXPECTED_AUDIO_FILE" >> "$PROMPT_MAP_FILE"
    fi
fi

