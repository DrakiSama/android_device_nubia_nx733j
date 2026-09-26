# Adaptador de build: activación explícita

Fecha: 2026-09-26. Estado: adaptador presente, **build no ejecutado**. El guard
de compilación cambia de «archivo ausente» a «entradas privadas obligatorias y
verificables»: `BoardConfigBringup.mk` ya existe y detiene el make con un error
explícito si faltan las entradas. No hay ROM compilada ni flasheable.

## Qué conecta el adaptador

| Área | Variables fijadas | Evidencia |
| --- | --- | --- |
| Kernel | `TARGET_PREBUILT_KERNEL`, `BOARD_KERNEL_IMAGE_NAME`, no-strip de módulos | [KERNEL-PROVIDER](KERNEL-PROVIDER.md) |
| DTB | `BOARD_INCLUDE_DTB_IN_BOOTIMG`, `BOARD_PREBUILT_DTBIMAGE_DIR` | [BUILD-PROVIDER-MAPPING](BUILD-PROVIDER-MAPPING.md) |
| DTBO | `BOARD_PREBUILT_DTBOIMAGE` (contenedor de 18 MiB) | [DTBO-AVB-ENVELOPE](DTBO-AVB-ENVELOPE.md) |
| Bootconfig | `BOARD_BOOTCONFIG_FILE` (232 bytes stock) | [BOOT-AUDIT](BOOT-AUDIT.md) |
| Vendor ramdisk | módulos stock + listas de carga normal (106) / recovery (303) | [RAMDISK-LOAD-AUDIT](RAMDISK-LOAD-AUDIT.md) |
| AVB | cadena completa con 7 claves de desarrollo y locations 1-6 | [AVB-DEV-KEYS](AVB-DEV-KEYS.md) |
| Perfil preservado | `-include $(NX733J_PRESERVED_MK)`; descriptores de las 4 imágenes en vbmeta | [PRESERVED-PROFILE-INTEGRATION](PRESERVED-PROFILE-INTEGRATION.md) |

## Entradas privadas

- `NX733J_PROVIDER_DIR`: paquete stock verificado. Preparación local con
  `tools/prepare_build_inputs.sh <provider-dir> <dtb-file> <dtbo18-file> <destino>`.
- `NX733J_AVB_KEYS_DIR`: claves RSA-4096 de desarrollo generadas con
  `tools/generate_dev_avb_keys.sh` (7 claves, ver registro público).
- `NX733J_PRESERVED_MK` (opcional): fragmento privado con las cuatro
  `BOARD_PREBUILT_*IMAGE`; sin él, esas particiones se intentarían construir
  desde el vendor repo generado.
- `proprietary-files.txt`: presente y **sin entradas** para el primer arranque
  ([selección](BOOT-DEPENDENCY-SELECTION.md)). `extract-files.py` genera el
  andamiaje del vendor repo; no se hereda el volcado antiguo de `~/lineage`.

## Pendientes antes del primer arranque

1. **Fstab de primera etapa y metadatos depmod** del vendor ramdisk
   (`modules.dep/alias/softdep/blocklist`). Este `build/make` no expone
   copy-out de archivos extra al vendor ramdisk; el mecanismo se resolverá sin
   copiar el fstab stock en bloque ([VENDOR-RAMDISK-LAYOUT](VENDOR-RAMDISK-LAYOUT.md)).
2. **VINTF/FCM y SEPolicy fuente** (bloque de compatibilidad).
3. **CRC del kernel base** (3404 pendientes) si se cambia el proveedor.

## Validación prevista de la primera compilación

- Comparar cabeceras `mkbootimg` de boot/init_boot/vendor_boot con
  [BOOT-BUILD-COMPOSITION](BOOT-BUILD-COMPOSITION.md).
- `avbtool info_image` sobre vbmeta, vbmeta_system, boot, init_boot,
  vendor_boot, recovery y dtbo: cadena, locations y descriptores.
- `dtb.img` idéntico al DTB stock preparado; `modules.load`/`modules.load.recovery`
  contra las listas de referencia; imágenes preservadas idénticas al manifiesto.
- Errores de cableado de variables se corrigen en esa corrida; el adaptador no
  se declara validado hasta entonces.

## Estado del entorno local (2026-09-26)

- Árbol actual copiado a `~/lineage/device/nubia/nx733j` (rsync del repositorio,
  sin `.git`).
- Copias obsoletas de mayo renombradas y movidas **fuera** del checkout a
  `~/nx733j-stale-20260527/` (`device-nubia-nx733j`, `vendor-nubia-nx733j`);
  no se borró nada.
- Vendor repo regenerado con el manifiesto sin entradas:
  `vendor/nubia/nx733j/{nx733j-vendor.mk,BoardConfigVendor.mk,Android.bp}`.
- Entradas privadas en `~/nx733j-build-inputs`; claves en
  `~/nx733j-avb-keys-20260926b`; variables en `~/nx733j-build-env.sh`.
- `lunch lineage_nx733j-trunk_staging-userdebug` completó con esas variables
  (configuración parseada; **no se compiló**).

### Hallazgo: el checkout es LineageOS 22.2, no 23.2

`~/lineage` usa el manifest `lineage-22.2` (`vendor/lineage/config/version.mk`:
22.2; `lunch` produjo `LINEAGE_VERSION=22.2-…`). El árbol de dispositivo y su
documentación apuntan a **lineage-23.2**. Consecuencias: las verificaciones de
interfaz registradas (BUILD-PROVIDER-MAPPING, PRESERVED-PROFILE-INTEGRATION) se
hicieron contra este checkout 22.x y deben re-verificarse contra 23.2 antes de
confiar en ellas.

**Decisión tomada (2026-09-26):** crear `~/lineage-23.2` como directorio nuevo
(el 22.2 queda intacto para referencia). El manifest 23.2 tiene 1166 proyectos:
290 desde `github.com/LineageOS` y **876 desde `android.googlesource.com`**.
Se detectó que WSL (NAT) no alcanzaba googlesource (503/TLS cortado) mientras
Windows sí; se activó **red espejo** en `C:\Users\draki\.wslconfig`
(`networkingMode=mirrored`, `dnsTunneling=true`) y, tras `wsl --shutdown`,
`git ls-remote` a googlesource funciona desde WSL. El `repo sync` corre en
segundo plano con log en `~/lineage-23.2-sync.log`.

Tras completar el sync: copiar este árbol a `~/lineage-23.2/device/nubia/nx733j`,
regenerar el vendor repo, **re-verificar las interfaces contra 23.2** y repetir
`lunch`; recién entonces la primera compilación, con autorización explícita.

## Límites

El adaptador no demuestra compilación, arranque, aceptación AVB del bootloader
ni compatibilidad VINTF. No activa OTA ni instalación. Los ficheros de licencia
de las imágenes preservadas se reubican a system (comportamiento del build,
`core/Makefile:2127`).
