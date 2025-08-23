#!/bin/bash

# play_video.sh - Descarga o reproduce videos de YouTube en Linux Mint (Celluloid)
# Opciones: -d (descargar), -p (descargar y reproducir, default), -s (streaming inmediato)
#           -r resolución (default 480p, ej: 720, 1080)

DOWNLOAD_DIR="$HOME/disco_externo/videos"
sudo chown jorge:jorge "$DOWNLOAD_DIR"
mkdir -p "$DOWNLOAD_DIR"

export PATH="$HOME/.local/bin:$PATH"

# --- FUNCIONES ---

usage() {
    echo "Uso: $0 [-d|-p|-s] [-r resolucion] <término de búsqueda>"
    echo "  -d : solo descargar"
    echo "  -p : descargar y reproducir después (default)"
    echo "  -s : streaming inmediato"
    echo "  -r : resolución (default 480)"
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
        printf "\r[%c] Descargando..." "${spin:$i:1}"
        sleep $delay
    done
    printf "\r[✔] Descarga completa!     \n"
}

sanitize_filename() {
    local filename="$1"
    filename="${filename// /_}"
    filename="${filename,,}"
    filename=$(echo "$filename" | iconv -f UTF-8 -t ASCII//TRANSLIT 2>/dev/null)
    filename=$(echo "$filename" | sed 's/[^a-zA-Z0-9_.-]//g')
    echo "$filename"
}

# --- PARÁMETROS ---
MODE="p"    # default: download & play
RES="480"

while getopts "dpsr:" opt; do
  case $opt in
    d) MODE="d" ;;
    p) MODE="p" ;;
    s) MODE="s" ;;
    r) RES="$OPTARG" ;;
    *) usage ;;
  esac
done
shift $((OPTIND -1))

if [ -z "$1" ]; then
    usage
fi

SEARCH_TERM="$*"

echo "Buscando en YouTube: $SEARCH_TERM"

# Obtener metadata
METADATA=$(yt-dlp --dump-json --default-search "ytsearch" "$SEARCH_TERM" 2>/dev/null | head -n 1)
VIDEO_TITLE=$(echo "$METADATA" | jq -r '.title')
VIDEO_URL=$(echo "$METADATA" | jq -r '.webpage_url')

BASE_FILENAME_SANITIZED=$(sanitize_filename "$VIDEO_TITLE")
EXPECTED_VIDEO_FILE="$DOWNLOAD_DIR/${BASE_FILENAME_SANITIZED}_${RES}p.mp4"

echo "Título: $VIDEO_TITLE"
echo "URL: $VIDEO_URL"
echo "Resolución: ${RES}p"

case "$MODE" in
  d) # Solo descargar
     yt-dlp -f "bestvideo[height<=$RES]+bestaudio/best[height<=$RES]" \
        -o "$EXPECTED_VIDEO_FILE" "$VIDEO_URL" >/tmp/yt-dlp.log 2>&1 &
     spinner $!
     wait
     echo "Video descargado en $EXPECTED_VIDEO_FILE"
     ;;
  p) # Descargar y reproducir
     yt-dlp -f "bestvideo[height<=$RES]+bestaudio/best[height<=$RES]" \
        -o "$EXPECTED_VIDEO_FILE" "$VIDEO_URL" >/tmp/yt-dlp.log 2>&1 &
     spinner $!
     wait
     echo "Video descargado en $EXPECTED_VIDEO_FILE"
     mpv --vo=gpu "$EXPECTED_VIDEO_FILE" >/dev/null 2>&1 &
     ;;
  s) # Streaming inmediato
     echo "Reproducción en streaming..."
     mvp --vo=gpu "$VIDEO_URL" >/dev/null 2>&1 &
     ;;
esac
