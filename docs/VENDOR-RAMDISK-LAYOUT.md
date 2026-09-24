# Vendor ramdisk y alcance del fstab

Fecha: 2026-09-24. [Inventario](../stock/vendor-ramdisk-layout-audit.json) obtenido
 del ramdisk LZ4 cuyo hash coincide con el proveedor stock.

## Contenido confirmado

- 306 módulos; hashes coincidentes con el manifiesto. Todos uid/gid 0:0, modo
  0644, nlink 1.
- Siete archivos adicionales: `first_stage_ramdisk/fstab.qcom` y seis archivos
  `lib/modules/modules.*`; todos 0:0, 0644, nlink 1.
- Tres directorios, 0:0, 0755. No hay scripts init ni ueventd ni ejecutables
  de espacio de usuario dentro de este vendor ramdisk.
- fstab.qcom: 7503 bytes, idéntico a la referencia publicada al normalizar LF.
- CPIO newc no representa xattrs SELinux. Los modos y propietarios comprobados
  no demuestran las etiquetas que tendrá una imagen reconstruida.

## Selección de entradas

El fstab tiene 25 entradas activas; 14 llevan `first_stage_mount`:

| Grupo | Filas | Observación |
| --- | --- | --- |
| Siete particiones lógicas | 8 | system tiene alternativas EROFS y ext4 |
| boot/init_boot/vendor_boot/dtbo/recovery | 5 | emmc: se usan para descubrir dispositivos AVB, no como filesystems montables |
| metadata | 1 | F2FS, con check y formattable |

REFERENCE: `system/core`, fuentes y hashes en `stock/build-interface-reference.json`.
PURPOSE: entender qué hará el init ROM con estas entradas, sin atribuir a su
binario el comportamiento exacto del init OEM.

`init/first_stage_mount.cpp:149–162` filtra por first_stage_mount cuando usa el
fstab de archivos; primero intenta fstab desde DT. Las entradas emmc se omiten
al montar (:623–628), pero permiten descubrir dispositivos para las cadenas AVB.
No eliminarlas sólo porque no son ext4/EROFS.

[CONFIRMED por lectura de código] Primera etapa tolera el fallo de una entrada
formattable (:636–638). Segunda etapa puede intentar formato tras fallar el
montaje si detecta partición borrada o cifrado interrumpido (`fs_mgr.cpp:1634–1675`).
Por eso no se instala automáticamente el fstab stock completo como configuración
ROM/recovery. Incluye formattable para metadata, persist, data, qmcs, spunvm y
logdump. No se ejecutó mount, fsck, formato ni recovery.

Las entradas sdcard1/usbotg y demás filas tardías no prueban por sí solas que el
hardware exista o que el sistema las use; quedan como referencia stock.

## Observación viva

[Montajes seleccionados](../stock/first-stage-mount-observation.json), slot B y
mismo arranque durante la consulta: `/` (system), system_ext, product, vendor,
odm, vendor_dlkm y system_dlkm usan EROFS; metadata usa F2FS. Los nombres dm-N
son temporales y no deben escribirse en fstab. No se capturaron datos de usuario.

## Claves alternativas de system

fstab enumera claves GSI q/r/s/t/u/v mediante avb_keys junto con avb=vbmeta_system.
El código local intenta las claves alternativas y puede recurrir a la cadena
AVB (:822–850). Su presencia no demuestra uso de GSI ni obliga a copiar claves
stock a una ROM. No se encontraron archivos /avb en los inventarios del
vendor ramdisk ni del init_boot B limpio; la política de claves ROM sigue abierta.

## Siguiente integración

Separar primera etapa y montaje tardío, mantener rutas lógicas/slotselect y
resolver AVB antes de instalar un fstab en el producto. Decidir explícitamente
la política ante errores de metadata/data y recuperación, conservando la copia
stock completa como referencia. El ramdisk de la ROM debe generar sus propias
etiquetas y su init; el contenido OEM tardío pertenece a otra etapa.

Reproducción (requiere lz4):

```text
python tools/audit_vendor_ramdisk_layout.py <vendor_ramdisk00> stock/kernel-provider-reference.json stock/first-stage-fstab.qcom <informe-nuevo.json>
```

No extrae archivos ni monta imágenes; rechaza destinos existentes.
