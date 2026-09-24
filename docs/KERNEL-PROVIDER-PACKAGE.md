# Paquete privado del proveedor stock

Estado: preparado el 2026-09-24, pendiente de integración al build.
La [evidencia de preparación](../stock/kernel-provider-preparation.json) identifica
el manifiesto privado por SHA-256. Los binarios no se publican en GitHub.

## Contenido y comprobaciones

| Tipo | Archivos |
| --- | ---: |
| Image, DTB, DTBO y referencias ramdisk/bootconfig | 5 |
| Módulos, conservados por partición | 681 |
| Metadatos de carga originales | 16 |
| Referencias de partición (incluidos avisos de licencia) | 8 |
| Listas de carga de referencia | 4 |
| Copia del manifiesto stock de referencia | 1 |

Son 715 archivos de payload, 203699992 bytes (aproximadamente 194 MiB), más el
archivo provider-manifest.json que los indexa. Los cinco artefactos y los 681
módulos coinciden con los hashes publicados en kernel-provider-reference.json.
Las listas se contrastan con sus hashes LF. Para cada archivo se compara además
SHA-256 del origen leído con el de la copia escrita. Los auxiliares se inventarían
por hash; esta operación no vuelve a autenticar una imagen de filesystem completa.

La copia incluye ambos zram/zsmalloc en sus particiones originales. init_boot y
las claves AVB no forman parte del proveedor de kernel; su integración pertenece
a la ROM. El ramdisk comprimido se conserva como referencia con sus metadatos
originales; los archivos sueltos del paquete no son una imagen lista para flashear.

## Preparar otro directorio privado desde las mismas capturas

Se requieren Python, lz4 y los módulos previamente extraídos. El destino debe ser
nuevo y quedar fuera de Git. Ejecutar desde la raíz del repositorio:

```sh
python3 tools/prepare_stock_kernel_provider.py stock/kernel-provider-reference.json /private/boot-unpacked /private/vendor_boot-unpacked /private/dtbo.img /private/dlkm /private/vendor/ifas.ko /private/new-provider
```

/private/dlkm contiene vendor_dlkm/ y system_dlkm/ completos de la extracción.
El script valida las entradas, crea el destino sin sobrescribir archivos y compara
los bytes escritos. Ante un error conserva el directorio parcial para inspección;
no borra nada y rechaza reutilizarlo. El manifiesto final solo se escribe cuando
todas las entradas esperadas quedaron copiadas y verificadas.

## Siguiente integración

Mapear este layout a las variables reales del build para boot/vendor_boot/DLKM,
preservando la separación entre kernel, plataforma NX733J y producto ROM. No se
ha añadido un adaptador de build ni se ha creado BoardConfigBringup.mk.
Siguen pendientes CRC del kernel base, política AVB/OTA y recuperación controlada.
La preparación de archivos no implica que haya una ROM compilable ni un boot probado.

La [revisión del build](BUILD-PROVIDER-MAPPING.md) detectó diferencias de entrada
DTB y de empaquetado AVB para DTBO. El paquete permanece intacto; no se activó
un adaptador que lo consuma automáticamente.
