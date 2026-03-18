#!/bin/bash

# Script para sincronizar el archivo NETWORK_MAP.md a todos los dispositivos Linux accesibles vía Tailscale
FILE_TO_SYNC="$HOME/NETWORK_MAP.md"

if [ ! -f "$FILE_TO_SYNC" ]; then
    echo "❌ ERROR: No se encontró el archivo $FILE_TO_SYNC en este equipo."
    exit 1
fi

# Lista de hosts (alias configurados en ~/.ssh/config o que responden en Tailscale)
# Puedes ir agregando más hosts en el futuro aquí.
NODES=("raspberrypi" "iqual-mint" "rv420" "net-1000h" "jorge-1000h")

echo "====================================================="
echo "🔄 Iniciando sincronización de $FILE_TO_SYNC"
echo "====================================================="

CURRENT_HOSTNAME=$(hostname)

for node in "${NODES[@]}"; do
    # Evitar sincronizar con el propio equipo usando el nombre de host como filtro rústico
    if [[ "$CURRENT_HOSTNAME" == *"$node"* ]]; then
        echo "⏭️  Saltando $node (es el equipo actual)."
        continue
    fi
    
    echo -n "Consultando a $node... "
    # Comprobar si el nodo está en línea y accesible por SSH rápidamente
    if timeout 3 ssh -q -o ConnectTimeout=2 "$node" "echo ok" >/dev/null 2>&1; then
        echo "✅ ONLINE. Copiando..."
        
        # Copiar el archivo directamente a la raíz del home del usuario remoto
        scp -q -o ConnectTimeout=2 "$FILE_TO_SYNC" "$node:~/"
        
        if [ $? -eq 0 ]; then
            echo "   -> Transferencia exitosa a $node."
        else
            echo "   -> ❌ Error en la transferencia a $node."
        fi
    else
        echo "❌ OFFLINE o inalcanzable."
    fi
    echo "-----------------------------------------------------"
done

echo "✅ Sincronización finalizada. El archivo NETWORK_MAP.md está actualizado en los equipos disponibles."
