#!/usr/bin/env bash
# Genera las claves RSA de desarrollo para AVB del NX733J y sus metadatos
# publicos (pkmd). Las claves privadas quedan SOLO en el destino local:
# nunca se copian al repositorio ni se publican.
#
# uso: generate_dev_avb_keys.sh <directorio-destino> <avbtool.py>
#   - rechaza un destino existente (no sobrescribe intentos previos)
#   - requiere openssl y python3
#   - genera: root, boot, recovery, vbmeta_system (RSA 4096)
#   - escribe manifest.txt en el destino (hashes pkmd y datos de la corrida)
set -euo pipefail

usage() { echo "uso: $0 <directorio-destino> <avbtool.py>" >&2; exit 2; }
[ $# -eq 2 ] || usage

DEST="$1"
AVB="$2"

[ -e "$DEST" ] && { echo "ERROR: $DEST ya existe; no se sobrescribe" >&2; exit 1; }
[ -f "$AVB" ] || { echo "ERROR: no existe $AVB" >&2; exit 1; }
command -v openssl >/dev/null || { echo "ERROR: falta openssl" >&2; exit 1; }
command -v python3 >/dev/null || { echo "ERROR: falta python3" >&2; exit 1; }

mkdir -p "$DEST"

for KEY in root boot recovery vbmeta_system; do
    openssl genrsa -out "$DEST/$KEY.pem" 4096
    chmod 600 "$DEST/$KEY.pem"
    python3 "$AVB" extract_public_key --key "$DEST/$KEY.pem" \
        --output "$DEST/$KEY.pkmd.bin"
done

{
    echo "# Claves AVB de desarrollo NX733J — registro local (no publicar los PEM)"
    echo "date_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "algorithm: RSA-4096"
    echo "avbtool: $AVB"
    echo
    echo "## SHA-256 de metadatos publicos (pkmd)"
    sha256sum "$DEST"/*.pkmd.bin
} > "$DEST/manifest.txt"

echo "OK: claves en $DEST"
echo "== pkmd SHA-256 =="
sha256sum "$DEST"/*.pkmd.bin
echo "Claves privadas: NO publicar; conservar este directorio como material sensible."
