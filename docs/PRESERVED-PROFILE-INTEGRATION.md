# Integración del perfil preservado: diseño verificado

Fecha: 2026-09-26. Estado: DESIGN_VERIFIED_NOT_ACTIVATED. No se incluyó el
fragmento privado, no se creó `BoardConfigBringup.mk` y no se compiló.
Complementa [BUILD-PROFILE](BUILD-PROFILE.md), [PRESERVED-IMAGE-INPUTS](PRESERVED-IMAGE-INPUTS.md),
[PROFILE-BLOB-SCOPE](PROFILE-BLOB-SCOPE.md) y [BUILD-PROVIDER-MAPPING](BUILD-PROVIDER-MAPPING.md).

## Interfaces del build verificadas (CONFIRMED)

Checkout local limpio y coincidente con las referencias registradas: `build/make`
en `ab5acb1281035ebc9b0f190baf22ef3ea896106e` y `vendor/lineage` en
`87f03bdeafbf22dc35130c61ae2ff97f2041b90f`. Líneas verificadas hoy:

| Ubicación | Efecto |
| --- | --- |
| core/Makefile:4089–4096 | Con `BOARD_PREBUILT_VENDORIMAGE`, `vendor.img` no se construye: `copy-one-file` del prebuilt a `$(PRODUCT_OUT)/vendor.img` |
| core/Makefile:4335, :4404, :4544 | Igual para odm, vendor_dlkm y system_dlkm |
| core/Makefile:2127–2131 | Con vendor prebuilt, los avisos de licencia se reubican en system |
| core/Makefile:6525, :6560, :6569, :6587 | target_files depende de las imágenes prebuilt (no de reglas de construcción) |
| core/Makefile:6944, :6972, :6976, :6984 | Las imágenes prebuilt se copian a `IMAGES/` dentro del zip target_files |
| core/board_config.mk:681, :707, :797, :816, :831, :850, :900, :919 | Rutas y variables de prebuilt reconocidas por la configuración de placa |

Consecuencia: las cuatro particiones preservadas conservan **byte por byte** las
imágenes privadas; nada del build las regenera ni les añade footer. La decisión
del perfil no altera `AB_OTA_PARTITIONS` por sí sola.

## Dónde se incluiría (DISEÑO; sin activar)

- El fragmento privado `BoardConfigPreservedImages.mk` (cuatro
  `BOARD_PREBUILT_*IMAGE`) no entra al repositorio: contiene rutas locales y las
  imágenes no se publican. Vive en `~/nx733j-preserved-inputs-20260925`.
- Punto de inclusión propuesto: `BoardConfigBringup.mk`, único guard de
  activación ya contemplado (`BoardConfig.mk:62–64`). Propuesta: terminar ese
  archivo con `-include $(NX733J_PRESERVED_MK)`, variable vacía por defecto y
  provista por el entorno de compilación; si está vacía, el perfil preservado no
  se activa. Descartado: incluir en `BoardConfig.mk` directo (rompe el guard y
  filtra una ruta privada) y copiar el fragmento al repositorio.
- Frontera del generador ([PROFILE-BLOB-SCOPE](PROFILE-BLOB-SCOPE.md)):
  `device.mk:8` hereda `vendor/nubia/nx733j/nx733j-vendor.mk` y
  `BoardConfig.mk:65` incluye `BoardConfigVendor.mk`. Con el perfil preservado
  el generador debe quedar acotado a dependencias externas de
  system/system_ext/product y **no** debe instalar archivos en
  vendor/odm/vendor_dlkm/system_dlkm. Ese modo no existe todavía:
  `extract-files.py:7–8` exige `proprietary-files.txt`, hoy ausente. Mientras no
  exista, ambos puntos permanecen bloqueados.
- El mecanismo multi-particion existe (el vendor generado antiguo contiene
  `system_ext/` y `product/`); lo que falta es la selección mínima, no el
  soporte de rutas.

## Particiones resultantes y tamaño

| Partición | Acción del perfil | Bytes | Identidad (inicio) |
| --- | --- | ---: | --- |
| vendor | preservar | 1940062208 | `814b348674…` |
| odm | preservar | 892928 | `a26ba138…` |
| vendor_dlkm | preservar | 33574912 | `12e553d4…` |
| system_dlkm | preservar | 7577600 | `7464f323…` |
| system | reconstruir EROFS | — | — |
| system_ext | reconstruir EROFS | — | — |
| product | reconstruir EROFS | — | — |
| boot / init_boot / vendor_boot / recovery | reconstruir | tamaños de partición ya en BoardConfig | — |
| dtbo | reempaquetar contenedor de 18 MiB | 18874368 de entrada | — |
| pvmfw | preservar B (solo descriptor) | 1048576 | `b4d3651a…` |
| vbmeta / vbmeta_system | reconstruir metadatos | — | — |

Cota de espacio con contenido stock del slot B (lpdump): system ≈ 4.52 GB,
system_ext ≈ 0.88 GB, product ≈ 1.98 GB y preservadas ≈ 1.98 GB suman ≈ 9.4 GB
sobre un grupo `qti_dynamic_partitions` de 17175674880 B (≈ 16 GiB): margen
amplio, pero los tamaños ROM de system/system_ext/product no se conocerán hasta
compilar. No se cambió geometría, grupo ni extents.

## AVB

- Las cuatro preservadas ya traen footer/hashtree propias; el vbmeta nuevo debe
  **incluir sus descriptores** (`avbtool --include_descriptors_from_image`) y no
  configurar reglas que añadan otro footer a esas particiones.
- `config/bringup-stock-b.json` fija `retain_matching_stock_hashtree_descriptor`
  y registra `descriptor_sha256` por partición (vendor `eda12369…`, odm
  `8818db9b…`, vendor_dlkm `fc70e1d1…`, system_dlkm `683bea22…`).
- pvmfw: descriptor solo si se conserva el firmware de ese slot (A y B
  difieren); `requires_destination_identity_check`.
- dtbo: descriptor recalculado desde el contenedor sin cambios.
- Claves: `null` en el contrato; sin decisión no hay build firmable. No usar
  claves OEM ni test keys como sustituto. No desactivar AVB.

## OTA

- `ota_enabled=false`; `AB_OTA_UPDATER=true` y `AB_OTA_PARTITIONS` (13 entradas,
  `BoardConfig.mk:31`) siguen provisionales. Virtual A/B con compresión XOR
  heredado (`device.mk:4`).
- target_files contendrá las cuatro imágenes prebuilt en `IMAGES/`
  (core/Makefile:6944–6985): la base para un payload futuro existe, pero claves,
  rollback, slot destino y aceptación del bootloader siguen UNKNOWN. Este perfil
  no genera paquete instalable.

## Hallazgo del checkout: extracción antigua sin auditar (CONFIRMED hoy)

`~/lineage` conserva el intento previo (mayo, anterior a las auditorías):

- `device/nubia/nx733j` con `prebuilt/kernel`, `prebuilt/boot.img`,
  `sepolicy/`, `system.prop`, `vendor.prop`, `recovery.fstab` y un BoardConfig
  que no es el auditado. No es la versión actual del repositorio.
- `vendor/nubia/nx733j` con un volcado completo sin auditar (~12 GB: system
  5.2G, product 2.8G, vendor 2.7G, system_ext 1.2G), `proprietary-files.txt`
  (492 KB) y `device-vendor.mk` (1.3 MB) generados con `gen_vendor.py`.
  Identidad/versión no verificadas; no es el perfil preservado ni la extracción
  actual, y su nombre generado no coincide con el que hereda el árbol actual
  (`nx733j-vendor.mk`).

Acciones requeridas antes de compilar: reemplazar el device tree instalado por
este repositorio (symlink o copia), no heredar el vendor antiguo, y decidir si
se conserva solo como evidencia local o se regenera acotado. No se movió ni
borró nada de ese checkout en esta sesión.

## Orden de activación propuesto

1. Aprobar política de claves/rollback y fstab/bootconfig/ramdisk.
2. Crear `BoardConfigBringup.mk` revisado: proveedor kernel, DTB/DTBO, ramdisk,
   AVB por partición y el `-include` del fragmento privado con variable
   explícita.
3. Implementar el modo acotado del generador y seleccionar dependencias mínimas
   de system_ext/product (empezando por boot/ADB).
4. Primera compilación (target_files); medir tamaños reales y comparar las
   imágenes preservadas contra el manifiesto privado.
5. Solo después: estrategia de instalación/recuperación con slot y comprobación
   de identidad por partición.

## Límites

Verificación de interfaces por lectura del checkout local en los commits
registrados; no se ejecutó make, no se copió ningún prebuilt y no se creó el
adaptador. La cota de tamaño usa contenido stock del slot B, no una medición de
imágenes ROM. Los hashes citados provienen del contrato y del manifiesto
privado; las imágenes no se publican.

## Reproducción

```text
# Verificación de interfaces (solo lectura)
git -C ~/lineage/build/make rev-parse HEAD
git -C ~/lineage/vendor/lineage rev-parse HEAD
grep -n BOARD_PREBUILT_VENDORIMAGE ~/lineage/build/make/core/Makefile
```

El script de esta sesión vivió fuera del repositorio y solo leyó archivos.
