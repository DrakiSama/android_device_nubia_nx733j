# Claves AVB de desarrollo: política y registro

Fecha: 2026-09-26. Estado: claves generadas localmente. No hay imágenes firmadas,
no se activó el build y no se autoriza instalación. Registro público de metadatos:
[`stock/dev-avb-keys-record.json`](../stock/dev-avb-keys-record.json).

## Decisión

El contrato [stock B](../config/bringup-stock-b.json) exige claves explícitas y
rechaza claves OEM o test keys como sustituto. Se adoptó una política de claves
**propias de desarrollo**, generadas con un script reproducible y custodiadas
fuera del repositorio. Es la opción elegida para poder construir y verificar la
cadena AVB en target_files sin publicar material sensible.

## Estructura generada

| Clave | Uso previsto | SHA-256 del pkmd |
| --- | --- | --- |
| root | firma del vbmeta raíz | `9fa07fb0…` |
| boot | footer AVB de boot | `9de53478…` |
| recovery | footer AVB de recovery | `35d11f41…` |
| vbmeta_system | vbmeta_system encadenado | `5f855796…` |

Algoritmo RSA-4096. Metadatos extraídos con `avbtool 1.3.0`
(`external/avb/avbtool.py`, commit `6ee41dc37ea996a250f5c70d0ea16abb9f169975`,
el mismo registrado en la auditoría del proveedor). Los hashes corresponden a
los ficheros `.pkmd.bin` (material público); los PEM privados nunca se copiaron
al repositorio.

## Política

- **Solo desarrollo**: las claves no son de release y deberán rotarse antes de
  cualquier uso público; no imitan claves OEM.
- **Rollback**: índice de desarrollo fijo y explícito (propuesta: `1`) que el
  adaptador fijará; no se copian índices stock (boot 3, recovery 1,
  vbmeta_system 2) ni se habilita descenso de versión.
- **Aceptación del bootloader: UNKNOWN.** El dispositivo está desbloqueado por
  una vía no convencional y no existe evidencia de que acepte estas claves;
  generarlas no valida ningún arranque firmado.
- **Sin OTA**: la firma de un paquete instalable queda fuera de alcance; el
  perfil sigue sin update_engine utilizable.
- **Custodia**: las claves viven en un directorio local fuera del repositorio
  (junto al manifest privado del fragmento preservado). Si se pierden antes de
  definir el producto, las pruebas incrementales con rollback se invalidan;
  regenerar produce una identidad de cadena nueva.

## Reproducir

```text
tools/generate_dev_avb_keys.sh <directorio-nuevo> ~/lineage/external/avb/avbtool.py
```

El script rechaza destinos existentes, exige `openssl` y `python3`, genera las
cuatro claves RSA-4096, extrae sus pkmd y escribe `manifest.txt` en el destino.
No copia nada al repositorio.

## Límites

- No se firmó ninguna imagen todavía: la conexión de claves a particiones
  (vbmeta, vbmeta_system encadenado, footers de boot/recovery, descriptores de
  las imágenes preservadas) corresponde al adaptador de build.
- La política de claves de release (incluida la aceptación por el bootloader)
  sigue abierta; este documento solo fija el material de desarrollo y su
  registro público.
