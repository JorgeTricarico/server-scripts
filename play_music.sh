
#!/bin/bash

# play_music.sh - Reproduce música de YouTube, con caché, metadatos y spinner
# Opciones: -d (descargar), -p (descargar y reproducir, default), -s (streaming inmediato)

# --- CONFIGURACIÓN ---
DOWNLOAD_DIR="$HOME/disco_externo/music"
PROMPT_MAP_FILE="$DOWNLOAD_DIR/prompt_song_map.txt"

mkdir -p "$DOWNLOAD_DIR"
touch "$PROMPT_MAP_FILE"

export PATH="$HOME/.local/bin:$PATH"

# --- FUNCIONES ---

usage() {
    echo "Uso: $0 [-d|-p|-s] <término de búsqueda>"
    echo "  -d : solo descargar"
    echo "  -p : descargar y reproducir después (default)"
    echo "  -s : streaming inmediato (no descarga)"
    exit 1
}

# Spinner minimalista
spinner() {
    local pid=$1
    local delay=0.1
    local spin='|/-\\'
    local i=0
    while kill -0 $pid 2>/dev/null; do
        i=$(( (i+1) %4 ))
        printf "\r[%c]" "${spin:$i:1}"
        sleep $delay
    done
    printf "\r[✔] Descarga completa!     \n"
}

# Limpia un string para usarlo como nombre de archivo
sanitize_filename() {
    local filename="$1"
    filename="${filename// /_}"
    filename="${filename,,}"
    filename=$(echo "$filename" | iconv -f UTF-8 -t ASCII//TRANSLIT 2>/dev/null)
    filename=$(echo "$filename" | sed 's/[^a-zA-Z0-9_.-]//g')
    filename=$(echo "$filename" | sed 's/__*/_/g; s/^_//; s/_$//')
    echo "$filename"
}

# Formatea duración en HH:MM:SS
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

# Reproduce una canción
play_song() {
    local file_path="$1"
    local song_name
    song_name=$(basename "$file_path")
    echo "Reproduciendo: $song_name"
    mpv --no-video "$file_path" >/dev/null 2>&1 &
    MPV_PID=$!
    echo "mpv iniciado con PID: $MPV_PID"
    echo "$MPV_PID" > /tmp/mpv_music.pid
}

# --- PARÁMETROS ---
MODE="p"   # default: download & play

while getopts "dps" opt; do
  case $opt in
    d) MODE="d" ;;
    p) MODE="p" ;;
    s) MODE="s" ;;
    *) usage ;;
  esac
done
shift $((OPTIND -1))

if [ -z "$1" ]; then
    usage
fi

SEARCH_TERM="$*" # Captura todos los argumentos

# Mostrar volumen actual (si tienes script propio)
echo ""
~/scripts/set_volume.sh
echo ""

# --- BÚSQUEDA EN CACHÉ ---
MATCHING_SONG_PATH=$(grep -Fm 1 "$SEARCH_TERM ::: " "$PROMPT_MAP_FILE" | cut -d ':' -f 4- | sed 's/^ *//;s/ *$//')

if [ "$MODE" != "s" ] && [ -n "$MATCHING_SONG_PATH" ] && [ -f "$MATCHING_SONG_PATH" ]; then
    echo "Prompt encontrado en caché!"
    if [ "$MODE" = "d" ]; then
        echo "Archivo ya descargado: $MATCHING_SONG_PATH"
        exit 0
    else
        play_song "$MATCHING_SONG_PATH"
        exit 0
    fi
fi

# --- BÚSQUEDA EN YOUTUBE ---
echo "Buscando en YouTube: $SEARCH_TERM"
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

BASE_FILENAME_SANITIZED=$(sanitize_filename "$VIDEO_TITLE")
EXPECTED_AUDIO_FILE="$DOWNLOAD_DIR/${BASE_FILENAME_SANITIZED}.mp3"

# --- MODO STREAMING ---
if [ "$MODE" = "s" ]; then
    echo "Reproducción en streaming..."
    mpv --no-video "$VIDEO_URL" >/dev/null 2>&1 &
    exit 0
fi

# --- DESCARGA ---
if [ -f "$EXPECTED_AUDIO_FILE" ]; then
    echo "El archivo ya existe!"
    if [ "$MODE" = "p" ]; then
        play_song "$EXPECTED_AUDIO_FILE"
    fi
else
    yt-dlp -f "bestaudio[ext=m4a]/bestaudio" \
        --extract-audio --audio-format mp3 --audio-quality 0 \
        --embed-metadata --embed-thumbnail --add-metadata \
        -o "$EXPECTED_AUDIO_FILE" "$VIDEO_URL" >/dev/null 2>&1 &
    YTDLP_PID=$!
    echo "Descargando..."
    spinner $YTDLP_PID
    wait $YTDLP_PID

    if [ -f "$EXPECTED_AUDIO_FILE" ]; then
        if [ "$MODE" = "p" ]; then
            play_song "$EXPECTED_AUDIO_FILE"
        fi
    else
        echo "Error: No se encontró archivo descargado."
    fi
fi

# --- GUARDAR EN CACHÉ ---
if [ -f "$EXPECTED_AUDIO_FILE" ]; then
    if ! grep -Fq "$SEARCH_TERM ::: $EXPECTED_AUDIO_FILE" "$PROMPT_MAP_FILE"; then
        echo "Guardando en caché..."
        echo "$SEARCH_TERM ::: $EXPECTED_AUDIO_FILE" >> "$PROMPT_MAP_FILE"
    fi
fi
