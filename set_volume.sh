#!/bin/bash

# Función para obtener el volumen actual del sink especificado
get_current_volume() {
    local sink_name="$1"
    local volume_output=""

    if [ "$sink_name" = "@DEFAULT_SINK@" ]; then
        # Para el sink por defecto, obtenemos la información general
        volume_output=$(pactl get-sink-volume @DEFAULT_SINK@ 2>/dev/null)
    else
        # Para sinks específicos (como Bluetooth), filtramos la lista
        volume_output=$(pactl list sinks | awk -v sink_name="$sink_name" '
            /Name: /{current_sink_name=$2}
            current_sink_name == sink_name && /^\s*Volume:/{print; exit}
        ')
    fi

    # Extraer el porcentaje del formato "X%".
    # Esto busca el primer número seguido de un '%' y lo extrae.
    echo "$volume_output" | grep -oE '[0-9]+%' | head -n 1 | sed 's/%//'
}


nivel="$1"

# Si no se proporciona un nivel, mostrar el volumen actual
if [ -z "$nivel" ]; then
    bluetooth_sink=$(pactl list sinks short | grep "bluez_sink" | awk '{print $2}')
    if [ -n "$bluetooth_sink" ]; then
        current_vol=$(get_current_volume "$bluetooth_sink")
        # Aseguramos que current_vol no esté vacío antes de imprimir
        if [ -z "$current_vol" ]; then current_vol="Desconocido"; fi
        echo "Volumen actual del parlante Bluetooth ($bluetooth_sink): ${current_vol}%"
    else
        current_vol=$(get_current_volume "@DEFAULT_SINK@")
        # Aseguramos que current_vol no esté vacío antes de imprimir
        if [ -z "$current_vol" ]; then current_vol="Desconocido"; fi
        echo "Volumen actual por defecto: ${current_vol}%"
    fi
    exit 0
fi

# Si se proporciona un nivel, proceder a establecerlo
# Verificar si el nivel es un número válido entre 0 y 100
if [[ "$nivel" =~ ^[0-9]+$ ]] && [ "$nivel" -ge 0 ] && [ "$nivel" -le 100 ]; then
    # Intentar encontrar el sink de audio Bluetooth activo
    bluetooth_sink=$(pactl list sinks short | grep "bluez_sink" | awk '{print $2}')

    if [ -n "$bluetooth_sink" ]; then
        # Si se encuentra un sink Bluetooth, establecer el volumen en ese sink
        pactl set-sink-volume "$bluetooth_sink" "$nivel%"
        echo "Volumen del parlante Bluetooth establecido a ${nivel}% ($bluetooth_sink)"
    else
        # Si no se encuentra un sink Bluetooth, intentar con el sink por defecto
        pactl set-sink-volume @DEFAULT_SINK@ "${nivel}%"
        echo "Volumen del sink por defecto establecido a ${nivel}%"
    fi
else
    echo "Error: valor de volumen inválido (${nivel}). Debe ser un número entre 0 y 100."
    exit 1
fi
