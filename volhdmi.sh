#!/bin/bash
# volhdmi.sh - Ajusta el volumen del audio HDMI de la Raspberry Pi
# Uso: ./volhdmi.sh <volumen>   (ejemplo: ./volhdmi.sh 80)

# Chequeo de parámetro
if [ -z "$1" ]; then
    echo "Uso: $0 <volumen 0-100>"
    exit 1
fi

VOLUME=$1

# Validar que sea número entre 0 y 100
if ! [[ "$VOLUME" =~ ^[0-9]+$ ]] || [ "$VOLUME" -lt 0 ] || [ "$VOLUME" -gt 100 ]; then
    echo "Error: el volumen debe ser un número entre 0 y 100"
    exit 1
fi

# Ajustar el volumen en la tarjeta HDMI (card 1, device 0)
amixer -c 1 sset 'HDMI' ${VOLUME}%
echo "Volumen HDMI ajustado a ${VOLUME}%"

