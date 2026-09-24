# Auditoría del respaldo 9008 NX733J

Fecha local: 2026-09-23. Árbol de referencia: `0590ddd`. Fuentes: respaldo del
propietario de 2026-05-04, capturas previas y observación del teléfono stock con
root. Las imágenes originales permanecen intactas, fuera de Git.
Los [informes JSON](../stock/edl-audit-2026-09-23/) contienen mediciones; su
[evidence-index.json](../stock/edl-audit-2026-09-23/evidence-index.json) identifica
cada informe por SHA-256. Los scripts locales y las imágenes no están publicados;
este conjunto no constituye por sí solo un procedimiento reproducible completo.

## Particiones y arranque

- [CONFIRMED] Seis LUN GPT: CRC de encabezados y entradas válidos, primario/backup
  coincidentes, 115 entradas contrastadas con XML, sin solapamientos de particiones.
  Los tamaños boot/init_boot/vendor_boot/recovery/dtbo/super concuerdan con BoardConfig.
- [CONFIRMED] Super: geometría válida, tres juegos de metadatos con sus backups,
  formato 10.2, sector liblp de 512 bytes y bloque lógico de 4096. Hay entradas COW
  y tablas históricas; no se deben combinar ni tratar como layout de instalación.
- [CONFIRMED] Los siete árboles AVB de particiones base B coinciden con el root
  digest del descriptor y con los bytes del árbol almacenado. FEC no verificado.
- [CONFIRMED] vendor/odm/system_ext/product base B coinciden por tamaño y SHA-256
  con las capturas anteriores. Esto no identifica automáticamente la vista de un
  snapshot activo en otro momento.
- [CONFIRMED] Firmas de vbmeta/vbmeta_system A/B válidas con sus claves incluidas;
  claves hijas boot/recovery/vbmeta_system coinciden con sus padres. Hashes propios
  boot/recovery válidos. [UNKNOWN] Confianza OEM y aceptación de rollback.
- [CONFIRMED] Recovery A/B usa header v4, kernel vacío y ramdisk propio.
- [CONFIRMED] El init stock B de 3245000 bytes coincide con el original conservado
  por Magisk en `.backup/init.xz`. La imagen instalada contiene init sustituido y
  overlays de Magisk: no sirve como prebuilt limpio sin distinguir su procedencia.

## Discrepancia zram/zsmalloc y observación del teléfono

El inventario ampliado contiene 681 archivos y 479 nombres de módulo únicos.
De 202 nombres repetidos, 200 tienen bytes idénticos; zram y zsmalloc tienen dos
variantes distintas. Los 471 nombres cargados de la captura anterior están
cubiertos; una coincidencia de nombre no identifica el binario cargado.

| Módulo | Build ID vendor_boot, vermagic 6.6.30 | Build ID system_dlkm, vermagic 6.6.92 |
| --- | --- | --- |
| zram | `1ba177010bd9be0cc57f14eca4f93ee690544c1b` | `814e2cb1387b81266c3a2e1b8686160c02a8e6c7` |
| zsmalloc | `1e3deb0414b3019d40324363ee5e322f3c3ea163` | `34d5315ed5ed2e8325977da00b25adc5a4a0471b` |

[CONFIRMED] En la lectura de sysfs del 2026-09-24 02:37 UTC (23 de septiembre en
Chile), slot B y kernel `6.6.92-android15-8-g3637f4904cf5-ab13944661-4k`, ambas notas
GNU coinciden exactamente con las variantes vendor_boot y difieren de system_dlkm.
Es identidad de compilación observada, no un hash de todos los bytes en memoria
ni una garantía para otros kernels. Los SHA-256 de los candidatos están en
[module-build-id-comparison.json](../stock/edl-audit-2026-09-23/module-build-id-comparison.json).

[CONFIRMED] Las listas stock de ramdisk incluyen zsmalloc en la línea 4 y zram en
la 68, tanto para boot como recovery. La lista normal tiene 106 entradas y su
cierre de dependencias modinfo está contenido en el ramdisk. La de recovery tiene
303 entradas y no debe copiarse como política normal de Android.

[CONFIRMED] En init.qti.kernel.rc, early-init ejecuta gki.modprobe antes de iniciar
vendor.modprobe. El script system_dlkm_modprobe.sh enumera archivos .ko y aplica
system_dlkm.modules.blocklist; no usa la lista modules.load de system_dlkm, que
está vacía. La blocklist observada no contiene zram ni zsmalloc. El cargador vendor
sí procesa modules.load y sus filtros. Los scripts OEM completos quedan locales.

[INFERRED] La carga temprana desde el ramdisk explica la identidad observada y es
coherente con las listas. No se capturó una traza completa de inserción de módulos.
Decisión: conservar las copias por partición y documentar el orden stock; no
seleccionar la variante de mayor versión ni deduplicar por nombre.

La consistencia de CRC importados del conjunto ampliado no verifica las
exportaciones del kernel. La auditoría anterior con modprobe cubrió los 306
módulos del ramdisk; no se extiende esa validación externa a los 681 archivos.

## Límites y siguiente paso

[UNKNOWN] Estado de merge actual, FEC, aceptación por bootloader y vía de
restauración. No se ejecutó flash_all.bat, no se escribió ninguna partición ni se
cambió de slot. El respaldo con COW no es una receta de flasheo universal.

Siguiente paso: documentar el contrato del proveedor de kernel/prebuilt y el mapa
de carga por partición, contrastando ABI/exportaciones antes de habilitar builds.
El [estado del bring-up](BRINGUP_STATUS.md) mantiene los bloqueos restantes.

## Estado vivo posterior

La [captura del 24 de septiembre](SNAPSHOT-STATE.md) compara los 14 mapas lineales
B/COW y las siete raíces verity con el respaldo. No observa targets de snapshot
activos; update_engine comunica IDLE. Esto actualiza el pendiente de observación
en vivo, sin demostrar restauración segura ni autorizar cambios sobre COW.
