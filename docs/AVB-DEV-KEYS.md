# Claves AVB de desarrollo: política y registro

Fecha: 2026-09-26. Estado: claves generadas localmente (conjunto v2, 7 claves).
No hay imágenes firmadas todavía. Registro público de metadatos:
[`stock/dev-avb-keys-record.json`](../stock/dev-avb-keys-record.json).

## Decisión

El contrato [stock B](../config/bringup-stock-b.json) exige claves explícitas y
rechaza claves OEM o test keys como sustituto. Se adoptó una política de claves
**propias de desarrollo**, generadas con un script reproducible y custodiadas
fuera del repositorio, para construir y verificar la cadena AVB completa en
target_files sin publicar material sensible.

El conjunto v1 (4 claves) queda superado por el v2 (7 claves), que cubre toda la
cadena de arranque. El directorio v1 permanece como material local de desarrollo
y ya no se referencia.

## Estructura generada (v2)

| Clave | Uso previsto | Location | SHA-256 del pkmd |
| --- | --- | ---: | --- |
| root | firma del vbmeta raíz | — | `d8aa10b1…` |
| boot | cadena de boot | 3 | `93805f89…` |
| recovery | cadena de recovery | 1 | `87a97584…` |
| vbmeta_system | cadena de vbmeta_system | 2 | `2aa4846b…` |
| init_boot | cadena de init_boot | 4 | `1a821313…` |
| vendor_boot | cadena de vendor_boot | 5 | `37a39519…` |
| dtbo | cadena de dtbo | 6 | `dabca8e2…` |

Algoritmo RSA-4096; índice de rollback de desarrollo fijo (`1`) para todas las
particiones. Las locations 1-3 reproducen el esquema stock; 4-6 son asignaciones
de desarrollo. Metadatos extraídos con `avbtool 1.3.0`
(`external/avb/avbtool.py`, commit `6ee41dc37ea996a250f5c70d0ea16abb9f169975`).
Los hashes corresponden a los `.pkmd.bin` (material público); los PEM privados
nunca se copiaron al repositorio.

## Política

- **Solo desarrollo**: las claves no son de release y deberán rotarse antes de
  cualquier uso público; no imitan claves OEM.
- **Rollback**: índice explícito `1`; no se copian índices stock (boot 3,
  recovery 1, vbmeta_system 2) ni se habilita descenso de versión.
- **Aceptación del bootloader: UNKNOWN.** No existe evidencia de que acepte
  estas claves; generarlas no valida ningún arranque firmado.
- **Sin OTA**: la firma de un paquete instalable queda fuera de alcance.
- **Custodia**: las claves viven en un directorio local fuera del repositorio;
  si se pierden antes de definir el producto, las pruebas incrementales con
  rollback se invalidan y regenerar produce una identidad de cadena nueva.

## Reproducir

```text
tools/generate_dev_avb_keys.sh <directorio-nuevo> ~/lineage/external/avb/avbtool.py
```

El script rechaza destinos existentes, exige `openssl` y `python3`, genera las
siete claves RSA-4096, extrae sus pkmd y escribe `manifest.txt` en el destino.
No copia nada al repositorio.

## Límites

- La conexión de claves a particiones vive en
  [BoardConfigBringup.mk](../BoardConfigBringup.mk) y se validará en la primera
  compilación (`avbtool info_image`); ver [BUILD-ADAPTER](BUILD-ADAPTER.md).
- La política de claves de release (incluida la aceptación por el bootloader)
  sigue abierta; este documento solo fija el material de desarrollo y su
  registro público.
