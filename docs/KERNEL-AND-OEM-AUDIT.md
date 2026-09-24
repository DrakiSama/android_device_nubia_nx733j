# Kernel y servicios OEM: auditoría 2026-09-23

## Kernel y módulos

Se compararon los 306 módulos del ramdisk capturado con sus hashes previos:
coinciden todos. De sus nombres, 305 aparecen entre los 471 módulos cargados
observados. Una coincidencia de nombre no identifica los bytes cargados.

Las tablas __versions contienen 3220 nombres de símbolos importados. No se
observan CRC contradictorios entre módulos para un mismo símbolo. Esto mide
consistencia interna del conjunto; NO demuestra coincidencia con las exportaciones
del kernel ni compatibilidad con un kernel recompilado. El parser se contrasta
con `modprobe --show-modversions` sin cargar los módulos; los resultados quedan en
`stock/kernel-module-audit.json`.

Configuración leída del kernel vivo: MODVERSIONS=y, MODULE_FORCE_LOAD desactivado,
MODULE_SIG=y, MODULE_SIG_PROTECT=y, MODULE_SIG_FORCE desactivado y
TRIM_UNUSED_KSYMS=y. No asumir que estas opciones permiten cualquier firma.
El taint observado es 4608 (warning y módulo externo), sin el bit de carga forzada.
El filtro de errores de símbolos/versiones no encontró coincidencias en el dmesg
actual; el buffer puede haber perdido mensajes anteriores.

Decisión: mantener el conjunto observado como referencia; no sustituirlo por las
fuentes OEM 6.6.30 solo por compartir modelo. Pendiente comparar exportaciones/CRC,
configuración, firmas y ABI del kernel que realmente usará la ROM.

Reproducir desde Linux con lz4 instalado:

```sh
python3 tools/audit_kernel_modules.py vendor_ramdisk00 stock/vendor-ramdisk-modules.json /ruta/proc-modules.txt /ruta/informe.json
```

La herramienta lee el CPIO en memoria, valida hashes y no extrae rutas ni carga
módulos. Las imágenes y módulos permanecen fuera de Git.

Referencias: [ABI/KMI de Android](https://source.android.com/docs/core/architecture/kernel/abi-monitor)
y [taint del kernel](https://docs.kernel.org/admin-guide/tainted-kernels.html).

## Servicios OEM: decisiones previas al port

Se inspeccionaron los init de las particiones extraídas:

| Componente | Evidencia | Decisión pendiente |
| --- | --- | --- |
| bootservice | boot-su consulta flag de actualización; boot-at consulta antirrobo; ambos root/oneshot/late_start | No incluir por defecto; comprobar si hace falta para hardware o solo funciones OEM |
| ssdaemon | late_start, root, socket sub-system-d y grupos radio/audio/log/nfc | Investigar dependencias con diagnóstico OEM antes de conservar o eliminar |
| vendorcfgd | Ejecuta vendorcfgdeamon, no vendorcfg; root, clase main, socket vendorcfgd | No confundir el ejecutable daemon con el cliente ELF previamente auditado |
| ssdaemon_vendor | Variantes QTI/MTK/SPRD y script selector; servicios deshabilitados de inicio | No copiar servicios de otras plataformas; revisar selector y clientes QTI |

bootservice, ssdaemon y el cliente vendorcfg dependen de libvendorcfg.oem.so.
La declaración init de vendorcfgd usa otro ejecutable; su necesidad no se deduce
de la dependencia ELF del cliente. No se modificó ningún servicio del teléfono.

Las evidencias completas de init/config/dmesg quedan localmente en
`diagnostics/rom-audit-2026-09-23/`. Este informe no habilita BoardConfigBringup.mk,
ni declara servicios portados, ni genera una imagen flasheable.
## Ampliación: respaldo 9008 y módulos DLKM

El [informe posterior](EDL-BACKUP-AUDIT.md) amplía el inventario a 681 archivos
y documenta dos variantes de zram/zsmalloc. Los build IDs de sysfs identifican
las variantes vendor_boot 6.6.30 en el arranque stock observado; se conservan
ambas copias por partición. Los límites del análisis de CRC anterior siguen vigentes.

## Exportaciones observadas del kernel y módulos cargados

Captura 2026-09-24 02:54 UTC, slot B, kernel
`6.6.92-android15-8-g3637f4904cf5-ab13944661-4k`.
Resultado: [kernel-export-name-audit.json](../stock/kernel-export-name-audit.json).

[CONFIRMED] Los 681 archivos auditados requieren 5089 nombres únicos registrados
en __versions. Todos aparecen entre los 12125 nombres __ksymtab observados en
/proc/kallsyms: 3404 con proveedor kernel y 1685 con proveedor módulo cargado.
No se publican direcciones de memoria. Antes de analizar cada módulo se contrastó
su SHA-256 con el inventario ampliado de la auditoría del respaldo.

Procedimiento local: leer /proc/config.gz y /proc/kallsyms con root; descomprimir
la configuración; recoger nombres __ksymtab_ y su propietario; extraer las tablas
__versions con tools/audit_kernel_modules.py; comparar conjuntos de nombres.
Las capturas y los scripts capture-kernel-interface.py/compare-export-names.py
permanecen en diagnostics/edl-backup-20260504-audit fuera del repositorio.

[CONFIRMED] Configuración observada: páginas ARM64 de 4 KiB, MODVERSIONS,
CFI_CLANG, MODULE_SIG, MODULE_SIG_PROTECT y TRIM_UNUSED_KSYMS activos;
MODULE_FORCE_LOAD y MODULE_SIG_FORCE desactivados. Las opciones ausentes del
archivo no se convierten automáticamente en valores negativos.

[UNKNOWN] Valores CRC de las exportaciones contrastados contra los imports,
compatibilidad ABI completa, namespaces y aceptación de firmas para sustituciones.
Las direcciones de símbolos __crc_ no se interpretan como valores CRC. Esta
comparación de __versions no es una auditoría de todos los símbolos ELF indefinidos.
Los módulos ya cargados pueden aportar símbolos que todavía no existen en una
fase anterior: el resultado no demuestra el cierre temporal del orden de carga.

## Seguimiento CRC (2026-09-24)

Los 3322 símbolos __crc_ visibles pertenecen a módulos, no al kernel base, y
son de tipo r. Los 11 marcadores consultados de tablas/texto tienen dirección
cero en esta captura. No se modificó la configuración del teléfono para exponerlas
ni se leyeron regiones de memoria del kernel. La búsqueda local acotada no encontró
Module.symvers, System.map o vmlinux; esto no demuestra su ausencia en otros discos.
Detalle: [kernel-crc-evidence-status.json](../stock/kernel-crc-evidence-status.json).

REFERENCE: Android Common Kernel, `android15-6.6-2025-07_r10`.
PURPOSE: localizar artefactos de la compilación GKI candidata, no sustituir el kernel.
La [entrada oficial de lanzamientos](https://source.android.com/docs/core/architecture/kernel/gki-android15-6_6-release-builds)
asocia el commit `3637f4904cf55eb3e7eccb9d747d754a4e199740` al build `13944661`,
coherente con la cadena de versión stock. [INFERRED] Equivalencia binaria: no se
obtuvo ni contrastó Image/Module.symvers oficial. Una URL candidata de symvers
respondió 404; no se convierte ese fallo en prueba de que el artefacto no exista.
El siguiente paso es obtener el artefacto exacto y comparar Image por SHA-256 antes
de usar sus CRC como evidencia del kernel NX733J.
