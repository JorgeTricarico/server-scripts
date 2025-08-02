#!/bin/bash

# Leer el PID desde el archivo temporal
if [ -f /tmp/mpv_music.pid ]; then
  pid=$(cat /tmp/mpv_music.pid)
  echo "Deteniendo mpv con PID $pid..."
  kill "$pid" 2>/dev/null # Intentamos matar el proceso, ignorando si ya no existe (redirigimos el error)
  rm /tmp/mpv_music.pid # Siempre eliminamos el archivo PID después de intentar matar el proceso
else
  echo "No se encontró reproducción activa."
fi
