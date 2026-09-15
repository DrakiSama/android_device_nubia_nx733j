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

1. Elegir kernel y módulos de la misma revisión. El kernel observado es 6.6.92;
   el archivo OEM local es 6.6.30. No se presume compatibilidad entre ambos.
2. Extraer boot/vendor_boot/dtbo y comprobar DTB, bootconfig, cargas tempranas
   y cadenas AVB antes de definir BoardConfigBringup.mk.
3. Completar proprietary-files.txt y extraer un dump stock organizado por
   particiones. Desde device/nubia/nx733j, ejecutar ./extract-files.py /ruta/dump
   con tools/extract-utils y sus dependencias disponibles.
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
