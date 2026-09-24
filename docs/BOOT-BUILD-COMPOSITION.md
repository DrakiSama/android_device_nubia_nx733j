# Composición de imágenes de arranque

Fecha: 2026-09-24. Alcance: interfaz del checkout ROM local y cabeceras NX733J
stock. No se compiló ni ejecutó mkbootimg para producir imágenes.

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
| boot | v4, kernel, sin ramdisk | Makefile:1420 excluye ramdisk cuando construye init_boot | Compatible en estructura; proveedor kernel pendiente de conectar |
| init_boot | v4, ramdisk genérico | board_config.mk:490 y Makefile:1633 | Se reconstruirá desde la ROM; no copiar init Magisk |
| vendor_boot | v4, DTB y ramdisk de plataforma | Makefile:1745–1769 | DTB listo; contenido ramdisk/cmdline/bootconfig pendientes |
| recovery | Partición independiente, v4, kernel vacío | BOARD_EXCLUDE_KERNEL_FROM_RECOVERY_IMAGE y argumentos heredados | No activar recovery-as-boot ni mover recursos a vendor_boot |

La variable BOARD_INCLUDE_DTB_IN_BOOTIMG dirige el DTB a vendor_boot cuando
este se construye y no hay vendor_kernel_boot. Su nombre no justifica colocar
el DTB físicamente en boot. No existe evidencia NX733J de vendor_kernel_boot.

La versión del SO y fecha de parche que genere la ROM son una decisión del
producto; no se fuerzan a los campos cero observados en boot stock. Tampoco se
copian fechas/firmas stock para aparentar una imagen oficial.

## Pendientes inmediatos

- Portar cmdline y bootconfig con procedencia y alcance; distinguir requisitos
  stock de capacidades OEM como QSPA y protected VM.
- Seleccionar los archivos de plataforma del vendor ramdisk, sus etiquetas,
  fstab y listas normal/recovery. No copiar el ramdisk stock entero como init ROM.
- Definir AVB por imagen, claves, rollback, alcance OTA y tratamiento pvmfw.
- Conectar el proveedor kernel sin acoplarlo a un derivado específico.

BoardConfigBringup.mk permanece ausente, bloqueando la construcción de imágenes.
Cambiar los argumentos documentados no demuestra un build correcto ni un boot.
Referencia del código: `stock/build-interface-reference.json`.
