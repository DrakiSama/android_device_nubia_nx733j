# CRC importados y exportados entre módulos NX733J

Fecha: 2026-09-24. Este informe amplía la comprobación de nombres exportados.
No incluye los valores CRC del kernel base.

## Resultado

[CONFIRMED] Se leyeron 681 archivos ELF cuyo SHA-256 coincide con
stock/kernel-provider-reference.json. El conjunto contiene 3322 nombres de
exportaciones de módulos. De los 5089 nombres importados versionados:

| Proveedor observado | Símbolos | Resultado |
| --- | --- | --- |
| Módulos stock | 1685 | CRC de importación y exportación coinciden, sin conflictos entre candidatos |
| Kernel base | 3404 | Nombres presentes; valores CRC todavía no comprobados |

Informe completo: [module-export-crc-audit.json](../stock/module-export-crc-audit.json).
Las copias con nombres repetidos permanecen separadas por partición, incluidas
las dos variantes de zsmalloc. Cada candidato del propietario observado debe
coincidir con todos los consumidores del símbolo; no se elige una copia por versión.

## Método y límites

La herramienta lee __versions y los símbolos __crc_ de ELF64 AArch64 relocatable.
Los CRC de exportación son uint32 contenidos en __kcrctab/__kcrctab_gpl. Comprueba
los límites y la cobertura exacta entre entradas CRC y símbolos __ksymtab_, y
rechaza tablas CRC con relocations o formatos no soportados. No interpreta una
dirección de /proc/kallsyms como CRC. No ejecuta los archivos .ko.

La captura runtime aporta propietarios por nombre. Esto no identifica los bytes
cargados de todos los módulos. La identidad por build ID ya contrastada para
zram/zsmalloc sigue teniendo el alcance documentado en EDL-BACKUP-AUDIT.md.
La igualdad de CRC no acredita namespaces, licencias, firmas, orden de carga ni
compatibilidad ABI completa. Este análisis de __versions tampoco cubre todos los
símbolos ELF indefinidos.

## Contraste independiente

Los 11 exports de system_dlkm/lib/modules/zsmalloc.ko coinciden con
`modprobe --show-exports`. La [evidencia de la muestra](../stock/module-export-crc-crosscheck.json)
registra su SHA-256 y los valores; este contraste externo cubre esa muestra,
no todos los archivos. La recaptura runtime conserva los mismos nombres y propietarios.

## Repetir con datos propios

Primero capturar nombres/propietarios del teléfono stock conectado y con `su`
previamente autorizado. La captura descarta direcciones y no cambia ajustes:

```sh
python3 tools/capture_kernel_exports.py /private/runtime-exports.json --adb adb
```

Con lz4 instalado, un ramdisk capturado y los archivos DLKM previamente extraídos:

```sh
python3 tools/audit_module_export_crcs.py \
  /private/vendor_ramdisk00 \
  /private/dlkm \
  /private/vendor/ifas.ko \
  stock/kernel-provider-reference.json \
  /private/runtime-exports.json \
  /private/module-crc-report.json
```

/private/dlkm contiene system_dlkm/ y vendor_dlkm/ con sus rutas lib/modules.
Las herramientas rechazan sobrescribir el informe. Un conflicto CRC genera el
informe y termina con código 2. Un hash o formato inesperado detiene el análisis;
no adaptar el manifiesto para ocultar la discrepancia.

## CRC del kernel base: pendiente

La compilación oficial candidata sigue siendo build13944661/kernel_aarch64.
El sitio reconoce ese build, pero los enlaces de artefactos consultados respondieron
404 y la consulta anónima del índice de artefactos respondió 403. El navegador
integrado tampoco pudo iniciar por un fallo de sandbox del entorno local.
No se obtuvieron Image/Module.symvers ni se comprobó equivalencia con stock.
Estos fallos no prueban que los artefactos no existan.

Se necesita el Image exacto y su Module.symvers o información equivalente; primero
contrastar SHA-256 del Image con la referencia stock, después comparar los 3404 CRC.
No se sustituyen por los de una compilación cercana ni se habilita carga forzada.
