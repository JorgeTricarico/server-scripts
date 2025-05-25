#!/bin/bash

# Leer el PID desde el archivo temporal
if [ -f /tmp/mpv_music.pid ]; then
  pid=$(cat /tmp/mpv_music.pid)
  echo "Deteniendo mpv con PID $pid..."
  kill "$pid" && rm /tmp/mpv_music.pid
else
  echo "No se encontró reproducción activa."
fi
