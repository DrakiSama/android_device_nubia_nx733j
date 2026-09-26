#!/usr/bin/env bash
# Prepara un directorio privado de entradas del build con enlaces a:
#   proveedor stock (kernel/Image, modules/, reference/), DTB .dtb y DTBO 18 MiB.
# uso: prepare_build_inputs.sh <provider-dir> <dtb-file> <dtbo18-file> <destino>
# Rechaza un destino existente; no copia binarios, solo crea enlaces.
set -euo pipefail

usage() { echo "uso: $0 <provider-dir> <dtb-file> <dtbo18-file> <destino>" >&2; exit 2; }
[ $# -eq 4 ] || usage

P="$1"; DTB="$2"; DTBO="$3"; DEST="$4"
[ -d "$P" ] || { echo "ERROR: no existe $P" >&2; exit 1; }
[ -f "$DTB" ] || { echo "ERROR: no existe $DTB" >&2; exit 1; }
[ -f "$DTBO" ] || { echo "ERROR: no existe $DTBO" >&2; exit 1; }
[ -e "$DEST" ] && { echo "ERROR: $DEST ya existe; no se sobrescribe" >&2; exit 1; }

mkdir -p "$DEST/kernel" "$DEST/dtb" "$DEST/dtbo" "$DEST/reference"
ln -s "$P/kernel/Image" "$DEST/kernel/Image"
ln -s "$DTB" "$DEST/dtb/$(basename "$DTB")"
ln -s "$DTBO" "$DEST/dtbo/dtbo.img"
ln -s "$P/reference/bootconfig" "$DEST/reference/bootconfig"
ln -s "$P/reference/modules.load.boot" "$DEST/reference/modules.load.boot"
ln -s "$P/reference/modules.load.recovery" "$DEST/reference/modules.load.recovery"
ln -s "$P/modules" "$DEST/modules"
ln -s "$P/provider-manifest.json" "$DEST/provider-manifest.json"

echo "== verificacion =="
for f in "$DEST/kernel/Image" "$DEST/dtb/$(basename "$DTB")" "$DEST/dtbo/dtbo.img" \
         "$DEST/reference/bootconfig" "$DEST/reference/modules.load.boot" \
         "$DEST/reference/modules.load.recovery"; do
    if [ -r "$f" ]; then echo "OK $f"; else echo "FALTA $f"; exit 1; fi
done
echo "modulos vendor_boot: $(find "$DEST/modules/vendor_boot/lib/modules" -name '*.ko' | wc -l)"
echo INPUTS_READY
