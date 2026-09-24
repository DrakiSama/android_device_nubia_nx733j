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

## Preparación acotada y nuevo hallazgo (2026-09-24)

- [CONFIRMED] Se preparó una copia privada `dtb/nx733j-stock.dtb` con los
  4487979 bytes íntegros y el SHA-256 stock indicado arriba. Esto resuelve la
  extensión de entrada del glob; no activa el adaptador ni demuestra un build.
- [CONFIRMED] DTBO: límites de las 37 entradas y cabeceras FDT válidos. El total
  de tabla, 14124069 bytes, coincide con el alcance del descriptor stock
  previamente verificado para esta misma captura.
- [CONFIRMED] Los 11041755 bytes posteriores contienen **234 bytes no nulos**.
  Por ello, la descripción anterior como relleno no implica ceros ni autoriza
  descartarlos. No se recortó DTBO.
- [UNKNOWN] Función y vigencia de esos bytes posteriores; pertenencia a otro
  contenedor o metadatos aún sin determinar. No se presupone corrupción.

Se detiene aquí la preparación DTBO por la regla del proyecto de reportar
 discrepancias antes de activar cambios. Siguiente: identificar las estructuras
posteriores y comparar con DTBO del respaldo 9008, sin escribir particiones.
El descriptor externo sólo cubre el prefijo indicado; no autentica toda esa zona.

### Restricción del empaquetador local

REFERENCE: `external/avb`, commit `6ee41dc37ea996a250f5c70d0ea16abb9f169975`.
PURPOSE: determinar el límite real de entrada del empaquetador ROM.
Archivo limpio; hash añadido a `stock/build-interface-reference.json`.

[CONFIRMED por lectura de código] `avbtool.py:2224` reserva 65536 + 4096 bytes;
`add_hash_footer`, líneas 3482–3512, sólo elimina datos usando un footer reconocido
al final y rechaza entradas mayores que partición menos esa reserva. Para
25165824 bytes de partición el máximo es **25096192 bytes**. La captura completa,
sin footer al final, excede ese límite en **69632 bytes**. No se ejecutó la regla:
es una incompatibilidad deducida del código y de las dimensiones verificadas,
no un fallo de compilación observado. Añadir `--do_not_append_vbmeta_image` por sí
solo no elimina esa comprobación. No se adoptó como solución.

### Reproducción de la preparación

```text
python tools/prepare_stock_dtb_input.py stock/kernel-provider-reference.json <proveedor-privado> stock/boot-audit.json <directorio-nuevo>
```

Rechaza destinos existentes; comprueba hashes DTB/DTBO antes de escribir.
Genera sólo una copia íntegra del DTB y un informe; conserva proveedor y respaldo.
No interpreta semántica de overlays ni crea un DTBO firmable.
[Resultado sin binarios](../stock/dtb-input-preparation.json).
