# Nubia NX733J — base de dispositivo Android

Árbol independiente de TWRP para Nubia Z70 Ultra NX733J / PQ84A01, con producto
LineageOS 23.2. La capa `nx733j.mk` se separa del wrapper `lineage_nx733j.mk`.
La adaptación a otras ROM, incluida crDroid, no está hecha.

## Estado

Revisión documental: 2026-10-23. Los artefactos y validaciones de build citados
abajo están registrados hasta el 2026-09-30; no pude reabrir WSL ni verificar
esos binarios en esta revisión. Antes de esta actualización documental, el repo local estaba sincronizado con
`origin/lineage-23.2`; el detalle del commit se registra en Git.

Se registran como completados offline:

- `bootimage vendorbootimage dtboimage` (2026-09-27), con comparaciones de
  kernel, DTB y payload DTBO contra stock.
- `target_files` y su auditoría de payload (2026-09-29).
- OTA `bacon` final (2026-09-30),
  `lineage-23.2-20260930-UNOFFICIAL-nx733j.zip`, 2.458.851.521 bytes,
  SHA-256 `fdf7202e5d1d48ae039c7d0515c446a57caab82fd0a114f481273f81baee01d5`.
- Matriz VINTF de 126 HAL y validación `checkvintf --check-compat`:
  `COMPATIBLE (rc=0)` contra vendor/odm stock.
- Vendor ramdisk con fstab de primera etapa sin `formattable`, blocklist,
  bootconfig y 306 módulos contrastados con referencias.

Estos resultados son de build o validación offline. **No hay ROM arrancada o
validada en el teléfono; la ROM no se ha flasheado.** La OTA está firmada con
claves de desarrollo; la aceptación del bootloader y la política de release no
están validadas.

La síntesis de pendientes y sus evidencias está en
[BRINGUP_STATUS](docs/BRINGUP_STATUS.md); el historial y los detalles del build,
en [BUILD-ADAPTER](docs/BUILD-ADAPTER.md). El build exige las entradas privadas
descritas en `BoardConfigBringup.mk`; no guardes sus claves ni binarios en Git.

## Pendientes antes de una prueba de instalación

- Completar la SEPolicy fuente y resolver el alcance AVB/OTA de release,
  incluido `pvmfw`, claves y rollback.
- Validar los requisitos de TWRP para vbmeta, particiones lógicas y selección
  de slot. El plan está en [FIRST-FLASH-PLAN](docs/FIRST-FLASH-PLAN.md).
- Completar el ensayo de restauración EDL y confirmar los prerequisitos de la
  ruta elegida antes de cualquier escritura.
- Arrancar y validar la ROM en el dispositivo con logs fechados.

El fastboot OEM está capado según la experiencia del usuario; el plan actual
considera EDL 9008 + TWRP. No se debe inferir seguridad de instalación a partir
de un build exitoso.

## Documentación de referencia

- [Auditoría de arranque stock](docs/BOOT-AUDIT.md),
  [composición de imágenes](docs/BOOT-BUILD-COMPOSITION.md) y
  [layout del vendor ramdisk](docs/VENDOR-RAMDISK-LAYOUT.md).
- [Selección de dependencias](docs/BOOT-DEPENDENCY-SELECTION.md),
  [auditoría ELF](docs/ELF-AUDIT.md),
  [contrato de kernel](docs/KERNEL-PROVIDER.md) y
  [perfil preservado](docs/BUILD-PROFILE.md).
- [Alcance AVB de pvmfw](docs/PVMFW-AVB-SCOPE.md),
  [claves AVB de desarrollo](docs/AVB-DEV-KEYS.md) y
  [plan de primer flasheo](docs/FIRST-FLASH-PLAN.md).

Los documentos fechados antes del 2026-09-30 describen auditorías o decisiones
de su fecha; consulta el estado vigente enlazado arriba antes de usar sus
pendientes históricos como instrucciones actuales.

## Repositorios

- ROM: [DrakiSama/android_device_nubia_nx733j](https://github.com/DrakiSama/android_device_nubia_nx733j)
- TWRP y OrangeFox son proyectos separados; sus árboles no se mezclan con este.
- El repositorio contiene fuentes, herramientas y metadatos, no dumps stock ni
  claves privadas.
