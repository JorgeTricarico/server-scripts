#!/bin/bash

# Dirección MAC de tu parlante Bluetooth
BLUETOOTH_MAC="41:42:85:F4:2B:DB"

# Nombre del sink de PulseAudio de tu salida de audio original (HDMI, 3.5mm, etc.)
# >>>>> DEBES ENCONTRAR ESTE NOMBRE EJECUTANDO 'pacmd list-sinks' CUANDO NO ESTE EL BT CONECTADO <<<<<
ORIGINAL_SINK_NAME="alsa_output.platform-3f00b840.mailbox.stereo-fallback" # <<<<< CAMBIA ESTO

echo "Intentando desconectar del parlante Bluetooth ($BLUETOOTH_MAC)..."

# Usamos bluetoothctl en modo interactivo para desconectar
bluetoothctl << EOF
disconnect $BLUETOOTH_MAC
quit
EOF

# Pequeña pausa
sleep 2

# Volver a la salida de audio original
echo "Restableciendo la salida de audio a $ORIGINAL_SINK_NAME..."
pacmd set-default-sink "$ORIGINAL_SINK_NAME"
echo "Parlante Bluetooth desconectado y salida de audio restablecida."
