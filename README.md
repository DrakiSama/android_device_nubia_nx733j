# Nubia NX733J — base de bring-up para LineageOS

Base independiente de TWRP. Referencia inicial: LineageOS `lineage-23.2`.
**No es todavía un árbol compilable ni un producto flasheable.**
La inclusión obligatoria de BoardConfigBringup.mk mantiene bloqueada la
compilación hasta resolver las decisiones pendientes. No se debe sustituir por
un archivo vacío para saltar esa validación.

## Lo preparado

Identidad, arquitectura, tamaños y grupo dinámico del teléfono real; producto
LineageOS; entrada para extract-utils Python; inventario de archivos vendor/odm,
HALs VINTF y listas stock de módulos. No hay partición odm_dlkm en este modelo.
Las listas stock se conservan como evidencia; no se cargan enteras en TWRP.

El inventario de blobs es una lista candidata, NO proprietary-files.txt de
producción: hay que separar los componentes que compila LineageOS, eliminar
duplicados, revisar dependencias ELF y añadir lo necesario de system_ext/product.
No se han copiado políticas SELinux compiladas como sustituto de su fuente.

## Siguiente trabajo obligatorio

1. Verificar KMI y símbolos del conjunto kernel/módulos. Se observó kernel 6.6.92
   y 306 módulos de ramdisk con vermagic 6.6.30-android15-8; los números de parche
   distintos no bastan para declarar compatibilidad ni incompatibilidad.
2. Ya se auditaron imágenes de arranque por lectura; ver docs/BOOT-AUDIT.md.
   Resolver init_boot limpio, KMI y política AVB/OTA antes de BoardConfigBringup.mk.
3. Completar proprietary-files.txt y extraer un dump stock organizado por
   particiones. Desde device/nubia/nx733j, ejecutar ./extract-files.py /ruta/dump
   con tools/extract-utils y sus dependencias disponibles. La clasificación
   reproducible de candidatos y sus pendientes están en docs/BLOBS-AUDIT.md.
4. Portar init, fstab Android, overlays, audio, cámara, radio, sensores, Wi-Fi,
   Bluetooth, biometría, GNSS, NFC, power y health, usando stock como evidencia.
5. Preparar SEPolicy fuente, compatibilidad VINTF y dependencias Qualcomm sun.
   No usar SELINUX_IGNORE_NEVERALLOWS ni fechas de parche ficticias de TWRP.
6. Verificar configuración/ELF/VINTF; luego compilar y probar con recuperación
   disponible. Una compilación exitosa no demuestra soporte de hardware.

El árbol OnePlus sm8750-common sirve para estudiar la integración de la plataforma,
no se hereda: DTB, firmware y configuraciones OEM no son intercambiables.

Referencias:
- https://github.com/LineageOS/android_device_oneplus_sm8750-common/tree/lineage-23.2
- https://lineageos.github.io/lineage_wiki/proprietary_blobs.html

## Auditoría de arranque (2026-09-15)

Ver [informe y decisiones pendientes](docs/BOOT-AUDIT.md) y
[hechos verificables](stock/boot-audit.json). Incluye listas de carga de arranque y
recovery, fstab de primera etapa y bootconfig extraídos como referencia; no se
instalan automáticamente en una ROM. Las imágenes quedan fuera de este repositorio.

Para comprobar que una captura corresponde a esta auditoría:
```sh
python3 tools/verify_boot_capture.py /ruta/a/la/captura
```
Esto comprueba tamaño, SHA-256 y encabezados; no valida firmas ni declara la ROM
compilable. La rama de desarrollo es `lineage-23.2`.

## Repositorio independiente y auditoría actual

Repositorio ROM: [DrakiSama/android_device_nubia_nx733j](https://github.com/DrakiSama/android_device_nubia_nx733j).
Su producto es LineageOS `lineage-23.2`; la adaptación a crDroid queda pendiente.
Los árboles de [TWRP](https://github.com/DrakiSama/twrp_device_nubia_nx733j) y
[OrangeFox](https://github.com/DrakiSama/orangeFox_device_nubia_nx733j) son proyectos separados.

La [auditoría ELF del 23 de septiembre](docs/ELF-AUDIT.md) cubre vendor, odm,
system_ext y product: 2393 ELF64 contrastados con readelf e inventario adicional
de 2621 archivos. Se registran dependencias pendientes, no soporte validado.
Solo se versionan fuentes, herramientas y metadatos; los dumps y binarios quedan
fuera del repositorio. Todavía no hay una ROM compilada ni instrucciones de flasheo.

La [auditoría de kernel y servicios OEM](docs/KERNEL-AND-OEM-AUDIT.md) registra la consistencia de CRC de los módulos y las decisiones pendientes de init.
