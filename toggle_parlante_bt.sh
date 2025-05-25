#!/bin/bash

# Dirección MAC de tu parlante Bluetooth
BLUETOOTH_MAC="41:42:85:F4:2B:DB"

# Nombre del sink de PulseAudio para tu parlante
BLUETOOTH_SINK_NAME="bluez_sink.41_42_85_F4_2B_DB.a2dp_sink"

# Nombre del sink de PulseAudio de tu salida de audio original
# >>>>> DEBES ENCONTRAR ESTE NOMBRE <<<<<
ORIGINAL_SINK_NAME="alsa_output.platform-3f00b840.mailbox.stereo-fallback" # <<<<< CAMBIA ESTO

# --- Verificar estado de conexión ---
# Intentamos obtener información del dispositivo y buscamos la línea 'Connected: yes'
# Capturamos la salida de error para que no se muestre si el dispositivo no se encuentra
DEVICE_INFO=$(bluetoothctl info $BLUETOOTH_MAC 2>/dev/null)
IS_CONNECTED=$(echo "$DEVICE_INFO" | grep 'Connected: yes')
SINK_EXISTS=$(pacmd list-sinks | grep "$BLUETOOTH_SINK_NAME")


# Consideramos "conectado" si bluetoothctl lo reporta como conectado Y PulseAudio tiene el sink
if [ -n "$IS_CONNECTED" ] && [ -n "$SINK_EXISTS" ]; then
    echo "Parlante Bluetooth ($BLUETOOTH_MAC) detectado como CONECTADO y sink activo. Desconectando..."
    # Ejecutar lógica de desconexión

    bluetoothctl << EOF
disconnect $BLUETOOTH_MAC
quit
EOF
    sleep 2
    pacmd set-default-sink "$ORIGINAL_SINK_NAME"
    echo "Parlante desconectado y salida restablecida a $ORIGINAL_SINK_NAME."

else
    echo "Parlante Bluetooth ($BLUETOOTH_MAC) detectado como DESCONECTADO o sink inactivo. Conectando..."
    # Ejecutar lógica de conexión

    bluetoothctl << EOF
connect $BLUETOOTH_MAC
quit
EOF
    sleep 5 # Espera un poco más al conectar

    # Verificar si la conexión fue exitosa después de intentar conectar
    IS_CONNECTED_AFTER_ATTEMPT=$(bluetoothctl info $BLUETOOTH_MAC 2>/dev/null | grep 'Connected: yes')

    if [ -n "$IS_CONNECTED_AFTER_ATTEMPT" ]; then
        echo "Conexión Bluetooth exitosa."
        pacmd set-default-sink "$BLUETOOTH_SINK_NAME"
        echo "Parlante configurado como salida por defecto."
    else
        echo "Fallo al conectar el parlante Bluetooth."
    fi
fi
