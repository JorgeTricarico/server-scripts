#!/bin/bash

nivel="$1"

# Verificar si el nivel es un número válido entre 0 y 100
if [[ "$nivel" =~ ^[0-9]+$ ]] && [ "$nivel" -ge 0 ] && [ "$nivel" -le 100 ]; then
    # Intentar encontrar el sink de audio Bluetooth activo
    bluetooth_sink=$(pactl list sinks short | grep "bluez_sink" | awk '{print $2}')

    if [ -n "$bluetooth_sink" ]; then
        # Si se encuentra un sink Bluetooth, establecer el volumen en ese sink
        pactl set-sink-volume "$bluetooth_sink" "$nivel%"
        echo "Volumen del parlante Bluetooth establecido a $nivel% ($bluetooth_sink)"
    else
        # Si no se encuentra un sink Bluetooth, intentar con el sink por defecto
        pactl set-sink-volume @DEFAULT_SINK@ "$nivel%"
        echo "Volumen del sink por defecto establecido a $nivel%"
    fi
else
    echo "Error: valor de volumen inválido ($nivel). Debe ser un número entre 0 y 100."
    exit 1
fi

