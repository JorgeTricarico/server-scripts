#!/bin/bash
# Pack de pruebas rápidas para Gemini Chat
echo -e "\033[94m[PRUEBA 1: Conectividad y Hostname]\033[0m"
chat -r "Responde solo con: Nodo=$HOSTNAME, Estado=OK"

echo -e "\n\033[94m[PRUEBA 2: Fecha y Año Dinámico]\033[0m"
chat "Dime la fecha y año actual según tu sistema."

echo -e "\n\033[94m[PRUEBA 3: Memoria de Sesión]\033[0m"
chat "Dime mi nombre si lo sabes, o salúdame."
