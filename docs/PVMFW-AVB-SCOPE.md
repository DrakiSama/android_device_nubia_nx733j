# pvmfw: formato, identidad por slot y alcance AVB

Fecha: 2026-09-24. Fuente NX733J: respaldo 9008 A/B, GPT y lectura actual mediante
ADB/root de tamaño y hash. [Auditoría](../stock/pvmfw-stock-audit.json) y
[identidad instalada](../stock/pvmfw-live-identity.json).

| Campo | A | B |
| --- | --- | --- |
| Partición física | pvmfw_a | pvmfw_b |
| Tamaño GPT y blockdev | 1048576 | 1048576 |
| Formato de contenedor | ANDROID!, header v3 | ANDROID!, header v3 |
| Ramdisk | 0 bytes | 0 bytes |
| Prefijo protegido por AVB | 630784 bytes | 778240 bytes |
| Coincide con vbmeta_system de su slot | Sí | Sí |
| Coincide respaldo con teléfono | Sí | Sí |

[CONFIRMED] A y B tienen hashes distintos. Ambos contienen footer AVB al final
de su partición y vbmeta interno de 640 bytes, algoritmo NONE. El descriptor
interno coincide con el externo de vbmeta_system; payloads coincidentes por hash.
La firma del padre fue auditada previamente; esto no prueba aceptación OEM.

El campo llamado kernel en este contenedor es parte del formato de pvmfw;
**no es el kernel Android del proveedor**. No aplicarle automáticamente el
header v4 de boot/vendor_boot/init_boot/recovery. No se extrajo ni ejecutó firmware.

## Efecto en la integración

REFERENCE: build/make, revisión en `stock/build-interface-reference.json`.
PURPOSE: identificar cómo puede entrar pvmfw en imágenes y descriptores ROM.

- `board_config.mk:924–928` habilita pvmfw mediante PRODUCT_BUILD_PVMFW_IMAGE.
- `Makefile:4550–4576` consume módulos pvmfw_img/pvmfw_bin y su clave embebida;
  activar la variable no significa reutilizar automáticamente el firmware NX733J.
- `Makefile:4996–4998` procesa AVB pvmfw sólo si existe su target instalado.
  Conservar bytes de una partición no garantiza que el nuevo vbmeta_system
  incluya su descriptor.

[INFERRED, condicionado al perfil] Si el nuevo vbmeta_system incluye el hash de
pvmfw B pero se instala en un slot que conserva pvmfw A, el descriptor no coincide:
las diferencias de hashes están confirmadas también en el teléfono. La resolución
debe definir identidad de firmware y slot destino; no basta decir conservar stock.
No se propone copiar B sobre A ni cambiar de slot para comprobarlo.

No importar todos los descriptores del vbmeta_system stock para conservar pvmfw:
contiene también hashes de system/product/system_ext que cambiarán al construir
la ROM. Hay que seleccionar el descriptor de pvmfw y generar los de imágenes nuevas.

## Decisiones abiertas

- Perfil inicial: qué particiones ROM se reconstruyen y qué firmware se conserva.
- Cómo exigir la identidad de firmware compatible para cada slot/OTA.
- Claves y cadena nuevas, rollback y aceptación del bootloader.
- Necesidad efectiva de protected VM para el primer arranque: bootconfig stock
  declara soporte, pero esta auditoría no ejecuta una VM ni demuestra su dependencia.

pvmfw no se añadió a AB_OTA_PARTITIONS, no se habilitó su build y no se publicó
ningún binario. Estas decisiones requieren un perfil AVB/OTA completo.

Reproducción de la auditoría de respaldo:

```text
python tools/audit_pvmfw_stock.py <avbtool.py> <images-del-respaldo> stock/edl-audit-2026-09-23/gpt-audit.json <informe-nuevo.json>
```
