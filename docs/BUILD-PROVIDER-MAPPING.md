# Integración del proveedor: diferencias antes de activar el build

Fecha: 2026-09-24. Se detuvo la activación del adaptador al encontrar diferencias
entre la interfaz del build local y la representación stock. No se modificó
BoardConfig.mk ni se creó BoardConfigBringup.mk.

REFERENCE: checkout local build/make, commit
`ab5acb1281035ebc9b0f190baf22ef3ea896106e`, y vendor/lineage, commit
`87f03bdeafbf22dc35130c61ae2ff97f2041b90f`.

PURPOSE: identificar consumidores reales de los artefactos del proveedor, sin
atribuir universalidad a variables específicas de LineageOS. Los archivos leídos
estaban limpios; [revisiones y hashes](../stock/build-interface-reference.json).

## Hallazgos y propuestas

| Archivo / sección | Problema o condición | Evidencia | Solución propuesta |
| --- | --- | --- | --- |
| build/make/core/Makefile:1089 | BOARD_PREBUILT_DTBIMAGE_DIR concatena únicamente *.dtb; el paquete usa dtb/dtb.img | Glob explícito frente al layout y SHA-256 del paquete | Preparar una entrada de trabajo con extensión .dtb y el payload íntegro; comprobar igualdad de bytes, sin dividir ni escoger árboles |
| build/make/core/board_config.mk:985 | Esa ruta requiere BOARD_INCLUDE_DTB_IN_BOOTIMG=true | Validación explícita del build | Resolver su colocación en vendor_boot según las reglas de header v4; no confundir el nombre de la variable con la partición final |
| build/make/core/Makefile:1101 | Con BOARD_AVB_ENABLE=true, BOARD_PREBUILT_DTBOIMAGE pasa por add_hash_footer | Regla copia y añade footer; stock carece de footer propio y tiene descriptor externo | No conectar directamente la captura completa; definir entrada de trabajo, política de firma/descriptor y tratamiento del relleno antes de activar |
| build/make/core/Makefile:703,709 | Las rutas vendor y vendor ramdisk habilitan staging de stripping salvo opción true | BOARD_DO_NOT_STRIP_VENDOR_MODULES y BOARD_DO_NOT_STRIP_VENDOR_RAMDISK_MODULES | Preservar bytes de los módulos stock usando los controles correspondientes en el futuro adaptador; comparar outputs con el manifiesto |
| vendor/lineage/build/tasks/kernel.mk:131-204 | TARGET_PREBUILT_KERNEL tiene aquí un consumidor de Lineage | Selección explícita entre prebuilt y kernel source | Mantener este enlace en la adaptación al producto; no presentarlo como contrato universal de AOSP |

La captura DTBO mide 25165824 bytes; la tabla ocupa 14124069 bytes y contiene
37 entradas verificadas. [INFERRED] Su relleno puede impedir el empaquetado esperado
por una regla que añade información AVB. No se ejecutó esa regla ni se generó un
DTBO alternativo: esto es un riesgo de integración identificado, no un fallo de
compilación observado ni evidencia de corrupción stock.

La conversión de nombre para DTB debe preservar el SHA-256 completo
`43ac35e516a10f61bdbc9ab264b66bcc2255ea4cafd50ce0923cad3b97cbba4b`.
La propuesta trata el payload como un bloque completo; no presupone cuántos árboles
internos contiene ni reutiliza DTB de otro dispositivo.

## Interfaces de carga ya identificadas

- BOARD_VENDOR_RAMDISK_KERNEL_MODULES y su lista normal se procesan por las reglas
  del ramdisk; BOARD_VENDOR_RAMDISK_RECOVERY_KERNEL_MODULES_LOAD produce la lista
  recovery separada. Preservar 106 entradas normales y 303 de recovery como referencia.
- BOARD_SYSTEM_KERNEL_MODULES_LOAD pasa a false cuando está vacío en este build.
  Es coherente con una lista stock vacía, pero no demuestra la política runtime:
  el cargador OEM enumeraba archivos .ko, como se documentó previamente.
- El proveedor preparado sigue siendo un conjunto privado de entradas; sus
  referencias de ramdisk y propiedades no se convierten automáticamente en archivos
  del producto ROM.

## Siguiente decisión concreta

Definir el empaquetado DTB/DTBO y la política AVB del producto antes de incluir un
adaptador de BoardConfig. Preservar el paquete stock ya verificado y preparar las
entradas de trabajo por separado. La elección de claves, descriptores, alcance OTA
y recuperación sigue abierta; no desactivar AVB para eludir esta decisión.

No se activó el build, no se ejecutó stripping y no se escribió el dispositivo.
