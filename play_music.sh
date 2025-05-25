#!/bin/bash

# Añadir entorno virtual yt-env al PATH
export PATH="$HOME/yt-env/bin:$PATH"

# Leer la búsqueda completa como una cadena
query="$*"

# Obtener la mejor URL de audio
url=$(yt-dlp -f bestaudio "ytsearch1:$query" --get-url)

# Verificar si se obtuvo una URL válida
if [[ -z "$url" ]]; then
  echo "No se pudo obtener la URL del audio."
  exit 1
fi

# Reproducir con mpv en segundo plano y guardar el PID
mpv "$url" > /dev/null 2>&1 &
echo $! > /tmp/mpv_music.pid
