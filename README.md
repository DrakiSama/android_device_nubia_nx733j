# Nubia NX733J — base de dispositivo Android

Base NX733J independiente de TWRP, orientada a AOSP y derivados.
El scaffold actual sigue siendo LineageOS `lineage-23.2`; su separación genérica
está pendiente. Estado vigente: [BRINGUP_STATUS](docs/BRINGUP_STATUS.md).
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

## Próximo trabajo: cerrar la base de arranque

1. Definir el perfil de particiones reconstruidas/conservadas y su política AVB.
   [pvmfw A/B](docs/PVMFW-AVB-SCOPE.md) tiene contenidos distintos también en el
   teléfono: conservar firmware exige precisar el slot y el descriptor esperado.
2. Conectar el proveedor kernel y las entradas privadas DTB/DTBO; integrar fstab,
   cmdline y bootconfig con procedencia. Revisar la política ante errores de
   metadata/data antes de instalar el fstab stock en la ROM.
3. Cerrar las dependencias mínimas vendor, VINTF y SELinux para habilitar el build.
   El inventario de blobs sigue siendo candidato; véase [BLOBS-AUDIT](docs/BLOBS-AUDIT.md).
4. Completar la comprobación ABI: 1685 CRC entre módulos coinciden, pero faltan
   3404 CRC del kernel base y otras condiciones. [Detalle](docs/MODULE-EXPORT-CRC.md).
5. Tras resolver lo anterior, compilar y planificar un primer arranque con una
   vía de recuperación comprobada. Hardware y adaptación específica a LineageOS
   quedan para sus etapas posteriores.

No usar SELINUX_IGNORE_NEVERALLOWS ni fechas de parche ficticias de recovery.
La lista completa de evidencia y pendientes está en [BRINGUP_STATUS](docs/BRINGUP_STATUS.md).

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

La [auditoría del respaldo 9008](docs/EDL-BACKUP-AUDIT.md) amplía GPT/super/AVB
y resuelve por build ID la identidad observada de zram/zsmalloc.

El [contrato del proveedor de kernel](docs/KERNEL-PROVIDER.md) separa artefactos,
módulos por partición e integración ROM. Su manifiesto stock registra hashes;
aún no activa un adaptador de build.

El [paquete privado stock](docs/KERNEL-PROVIDER-PACKAGE.md) está preparado con
verificación de hashes. GitHub contiene la herramienta y el informe, sin binarios.

## Avances de la base (2026-09-24)

- [DTBO](docs/DTBO-AVB-ENVELOPE.md): se corrigió la auditoría inicial; existe
  footer AVB dentro de un contenedor de 18 MiB en la partición de 24 MiB.
  Entrada privada preparada conservando el contenedor y la referencia original.
- [Empaquetado](docs/BOOT-BUILD-COMPOSITION.md): argumentos header v4 explícitos
  para boot/vendor_boot e init_boot, direcciones stock con base cero, y EROFS
  declarado para system/system_ext/product.
- [Vendor ramdisk](docs/VENDOR-RAMDISK-LAYOUT.md): contenido, propietarios, modos
  y semántica de fstab auditados. No se copió el fstab automáticamente al producto.
- [pvmfw](docs/PVMFW-AVB-SCOPE.md): tamaño, header v3, hashes y descriptores A/B
  contrastados con respaldo y teléfono. Integración AVB/OTA aún pendiente.

No se ejecutaron builds ni pruebas de la ROM durante esta tanda. Los cambios de
BoardConfig conservan el bloqueo deliberado; no existe todavía una imagen ROM
validada para instalar.
