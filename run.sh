#!/usr/bin/env bash
# Punto de entrada principal del proyecto.
# Uso: ./run.sh "<instruccion>"
# Ejemplo: ./run.sh "add x5, x6, x7"
#
# Este script invoca la versión final del codificador: un solo argumento con la
# instrucción y una línea de salida "HEX: 0x........" para validación por scripts.
set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo 'Uso: ./run.sh "<instruccion>"' >&2
    echo 'Ejemplo: ./run.sh "add x5, x6, x7"' >&2
    exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/encoder.py" "$1"
