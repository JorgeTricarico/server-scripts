#!/bin/bash

# Dirección MAC de tu parlante Bluetooth
BLUETOOTH_MAC="41:42:85:F4:2B:DB"

# Nombre del sink de PulseAudio para tu parlante (el que encontraste con pactl list sinks short)
BLUETOOTH_SINK_NAME="bluez_sink.41_42_85_F4_2B_DB.a2dp_sink"

echo "Intentando conectar al parlante Bluetooth Azul ($BLUETOOTH_MAC)..."

# Usamos bluetoothctl en modo interactivo para conectar
bluetoothctl << EOF
connect $BLUETOOTH_MAC
quit
EOF

# Pequeña pausa para dar tiempo a la conexión y al registro del sink en PulseAudio
sleep 5

# Verificar si el parlante está conectado (opcional, pero útil)
IS_CONNECTED=$(bluetoothctl info $BLUETOOTH_MAC | grep 'Connected: yes')

if [ -n "$IS_CONNECTED" ]; then
    echo "Conexión Bluetooth exitosa."

    # Establecer el parlante Bluetooth como sink por defecto
    echo "Estableciendo $BLUETOOTH_SINK_NAME como salida de audio por defecto..."
    pacmd set-default-sink "$BLUETOOTH_SINK_NAME"
    echo "Parlante Bluetooth configurado como salida por defecto."
else
    echo "Fallo al conectar el parlante Bluetooth."
fi
