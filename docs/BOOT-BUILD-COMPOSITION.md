# Composición de imágenes de arranque

Fecha: 2026-09-24. Este documento registra el análisis de interfaz/cabeceras
previo a los builds. Las imágenes se compilaron y auditaron después; el estado
actual de esa evidencia está resumido en [BUILD-ADAPTER](BUILD-ADAPTER.md).
Ninguno de esos builds demuestra un arranque en dispositivo.

## Omisiones corregidas en BoardConfig

| Archivo / sección | Problema | Evidencia | Cambio |
| --- | --- | --- | --- |
| BoardConfig.mk, header v4 | La variable de board no suministraba --header_version | Makefile pasa BOARD_MKBOOTIMG_ARGS; mkbootimg.py:487,542 usa 0 por defecto | Argumento v4 explícito |
| BoardConfig.mk, init_boot | Usa lista de argumentos distinta | Makefile:1642,1656 consume BOARD_MKBOOTIMG_INIT_ARGS | Argumento v4 también en esa lista |
| BoardConfig.mk, direcciones | Base predeterminada de mkbootimg es 0x10000000 | mkbootimg.py:518; direcciones stock mucho menores | Base cero y offsets explícitos que reproducen las direcciones stock |

[CONFIRMED] Direcciones almacenadas en vendor_boot stock:

| Campo | Valor |
| --- | --- |
| Kernel | 0x00008000 |
| Ramdisk | 0x01000000 |
| Tags | 0x00000100 |
| DTB | 0x01f00000 |

Fuente: `stock/boot-audit.json`, sección vendor_boot. El empaquetador escribe
`base + offset` en estos campos (mkbootimg.py:158,160,166,176). **Base cero es
una decisión de representación**, no un campo leído del firmware, y estos
valores no representan offsets para escribir particiones. Ninguno viene del NX789J.

## Distribución de componentes

| Imagen | Evidencia stock | Ruta del build local | Estado |
| --- | --- | --- | --- |
| boot | v4, kernel, sin ramdisk | Makefile:1420 excluye ramdisk cuando construye init_boot | Build acotado con kernel stock registrado; no validado en dispositivo |
| init_boot | v4, ramdisk genérico | board_config.mk:490 y Makefile:1633 | Se reconstruye desde fuentes ROM; no copiar init Magisk. Build OTA registrado, sin prueba de arranque |
| vendor_boot | v4, DTB y ramdisk de plataforma | Makefile:1745–1769 | Build registrado con DTB, fstab, blocklist, bootconfig y módulos auditados offline |
| recovery | Partición independiente, v4, kernel vacío | BOARD_EXCLUDE_KERNEL_FROM_RECOVERY_IMAGE y argumentos heredados | No activar recovery-as-boot ni mover recursos a vendor_boot |

La variable BOARD_INCLUDE_DTB_IN_BOOTIMG dirige el DTB a vendor_boot cuando
este se construye y no hay vendor_kernel_boot. Su nombre no justifica colocar
el DTB físicamente en boot. No existe evidencia NX733J de vendor_kernel_boot.

La versión del SO y fecha de parche que genere la ROM son una decisión del
producto; no se fuerzan a los campos cero observados en boot stock. Tampoco se
copian fechas/firmas stock para aparentar una imagen oficial.

## Estado y pendientes (actualizado 2026-10-23; validación offline hasta 2026-09-30)

- Bootconfig integrado (`BOARD_BOOTCONFIG` con las 7 líneas stock; bootconfig del vendor_boot registrado byte a byte idéntico al stock). La cmdline vacía corresponde al boot stock auditado.
- ~~Seleccionar archivos de plataforma del vendor ramdisk, fstab y listas~~: fstab de primera etapa integrado (sin `formattable`); blocklist stock verbatim; 306 módulos con hash de referencia; depmod generado.
- **AVB por imagen, claves, rollback, alcance OTA y tratamiento pvmfw**: imágenes/OTA de desarrollo firmadas en builds registrados con rollback 1; aceptación de bootloader, `pvmfw` y claves/política de release pendientes.
- **Conectar el proveedor kernel**: completado (prebuilt kernel stock, DTB, DTBO, módulos).
- Cadena AVB de desarrollo conectada en los builds registrados; pendiente decisión de release.
- BoardConfigBringup.mk **presente** desde commit `df9811a` (adaptador de build con entradas privadas obligatorias).

Referencia del código: `stock/build-interface-reference.json`.

## Imágenes lógicas: tipos explícitos

Se añadieron BOARD_SYSTEMIMAGE_FILE_SYSTEM_TYPE,
BOARD_SYSTEM_EXTIMAGE_FILE_SYSTEM_TYPE y BOARD_PRODUCTIMAGE_FILE_SYSTEM_TYPE
como EROFS. Evidencia: siete volúmenes del super auditado, fstab y observación
viva del mismo NX733J. No son valores heredados del recovery ni de NX789J.

`board_config.mk:725–739,765–779` utiliza los tipos product/system_ext para
habilitar sus imágenes separadas; enumerarlas en el grupo dinámico no basta.
El árbol ya tenía estas variables para vendor/odm y ambos DLKM.

La [configuración del kernel](../stock/kernel-filesystem-config.json) vuelve a
coincidir por SHA-256 con la auditada: EROFS, xattrs, ACL, etiquetas y ZIP están
habilitados; LZMA y DEFLATE están deshabilitados. El build local usa LZ4/LZ4HC
por defecto (Makefile:2247–2249). No se eligió un compresor alternativo ni se
cambiaron geometría, tamaños o extents stock. Falta medir tamaño de imágenes
ROM cuando el build sea habilitado; estas variables no prueban que quepan.
