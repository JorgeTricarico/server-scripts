#!/bin/bash

# Añadir entorno virtual yt-env al PATH
export PATH="$HOME/yt-env/bin:$PATH"

# Leer la búsqueda completa como una cadena
query="$*"

# Obtener la URL y el título del video
# Usamos --print "title" para obtener el título y --get-url para la URL
# Redirigimos stderr a /dev/null para suprimir las advertencias
output=$(yt-dlp -f bestaudio --print "title" --get-url "ytsearch1:$query" 2>/dev/null)

# Separar el título de la URL (el título es la primera línea, la URL la segunda)
title=$(echo "$output" | head -n 1)
url=$(echo "$output" | tail -n 1)

# Verificar si se obtuvo una URL válida
if [[ -z "$url" ]]; then
  echo "No se pudo obtener la URL del audio."
  exit 1
fi

# Imprimir el tema encontrado en la consola
echo "Reproduciendo: $title"

# Reproducir con mpv en segundo plano y guardar el PID
mpv "$url" > /dev/null 2>&1 &
echo $! > /tmp/mpv_music.pid
