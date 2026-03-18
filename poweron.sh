#!/bin/bash

CONFIG_FILE="$HOME/.config/poweron.conf"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "⚠️  No se encontró el archivo de configuración en $CONFIG_FILE."
    echo "Creando una plantilla..."
    mkdir -p "$HOME/.config"
    cat << 'EOF' > "$CONFIG_FILE"
# Archivo de configuración para poweron
# Agrega aquí las direcciones MAC de los dispositivos que quieres encender.
MACS=(
    # "XX:XX:XX:XX:XX:XX" # Dispositivo 1
)

# Equipos "puente" de Tailscale que suelen estar encendidos en las distintas redes
BRIDGES=(
    # "raspberrypi"
    # "iqual-mint"
)
EOF
    echo "✅ Plantilla creada. Por favor edita $CONFIG_FILE con tus datos y vuelve a ejecutar 'poweron'."
    exit 1
fi

# Cargar la configuración
source "$CONFIG_FILE"

# Si no hay MACs configuradas, avisar y salir
if [ ${#MACS[@]} -eq 0 ]; then
    echo "⚠️  No hay direcciones MAC configuradas en $CONFIG_FILE. Por favor agrega algunas."
    exit 1
fi

# Script en Python que se ejecutará en cada nodo para enviar el paquete mágico
PYTHON_SCRIPT='
import socket, binascii, sys
macs = sys.argv[1:]
if not macs:
    sys.exit()
for mac in macs:
    try:
        mac_bytes = binascii.unhexlify(mac.replace(":", ""))
        magic_packet = b"\xff" * 6 + mac_bytes * 16
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(magic_packet, ("255.255.255.255", 9))
    except Exception as e:
        pass
print(f"Paquetes WOL mágicos esparcidos exitosamente por la red a las MACs: {\", \".join(macs)}")
'

echo "====================================================="
echo "💻 1. Esparciendo WOL localmente desde este equipo..."
echo "====================================================="
python3 -c "$PYTHON_SCRIPT" "${MACS[@]}"

echo ""
echo "====================================================="
echo "🌉 2. Conectando a los puentes de Tailscale..."
echo "====================================================="
for bridge in "${BRIDGES[@]}"; do
    echo "Consultando a $bridge..."
    # Usamos un timeout corto de 3 segundos para no demorar si están apagados
    if timeout 3 ssh -q -o ConnectTimeout=2 "$bridge" "echo ok" >/dev/null 2>&1; then
        echo "✅ ¡$bridge está ONLINE! Esparciendo WOL en su red local..."
        ssh -q -o ConnectTimeout=2 "$bridge" "python3 -c '"$PYTHON_SCRIPT"' ${MACS[*]}"
    else
        echo "❌ $bridge está OFFLINE o inalcanzable."
    fi
    echo "-----------------------------------------------------"
done

echo "✅ Proceso completado."
