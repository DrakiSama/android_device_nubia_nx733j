# Contenedor AVB interno de DTBO

Fecha: 2026-09-24. Fuente: respaldo 9008 NX733J, imágenes A/B, y proveedor B.
[Informe reproducible](../stock/dtbo-avb-envelope-audit.json).

## Corrección de la auditoría inicial

[CONFIRMED] El footer existe al offset **18874304** y termina a **18874368 bytes
(18 MiB)**. La partición mide **25165824 bytes (24 MiB)**. Revisar únicamente sus
últimos 64 bytes produjo la conclusión inicial incorrecta de ausencia de footer.
El fallo de `avbtool info_image` sobre esa captura completa no detecta el footer
interno. La captura no está corrupta por esa razón.

| Campo | Slot A | Slot B |
| --- | --- | --- |
| Tabla DTBO / original_image_size | 13361082 | 14124069 |
| vbmeta_offset | 13361152 | 14127104 |
| vbmeta_size | 640 | 640 |
| Footer offset | 18874304 | 18874304 |
| Tamaño del contenedor con footer | 18874368 | 18874368 |
| Ceros posteriores hasta fin de partición | 6291456 | 6291456 |

[CONFIRMED] Ambos bloques internos son AVB de algoritmo **NONE**, sin firma ni
clave propia. Su único descriptor hash DTBO coincide en todos sus campos con
el descriptor del vbmeta externo de su slot. El hash calculado del payload con
su salt coincide. Las firmas de vbmeta padre se auditaron por separado; el
presente análisis no atribuye una firma propia al bloque interno.

[CONFIRMED] Los 234 bytes no nulos observados en la cola B pertenecen al bloque
vbmeta y al footer. Los espacios entre payload, vbmeta, footer y fin de partición
son ceros. DTBO B del respaldo y del proveedor coinciden byte a byte por SHA-256.
No se mezclaron payload ni descriptores entre slots.

[UNKNOWN] Si el bootloader consulta este footer interno o sólo el descriptor
externo, así como la política de aceptación de claves/rollback para una ROM.
El tamaño de 18 MiB describe el contenedor observado: **no sustituye el tamaño
real de partición de 24 MiB en BoardConfig o GPT**.

## Consecuencia para el build

El `add_hash_footer` local busca el footer al final de su entrada. Una copia de
trabajo que termine al final del contenedor stock conserva payload, vbmeta,
footer y sus espacios; sólo omite los 6 MiB finales comprobados como ceros.
El empaquetador puede entonces reconocer original_image_size antes de generar
su metadata nueva. Esta conclusión proviene del código; no se ejecutó un build
ni se firmó una imagen ROM.

La captura de partición permanece como referencia inmutable. La selección de
claves, salt de construcción, flags, rollback y alcance OTA no se hereda del
contenedor stock. No cambiar BOARD_DTBOIMG_PARTITION_SIZE para acomodar la entrada.

## Reproducción (sólo lectura)

```text
python tools/audit_dtbo_avb_envelope.py <avbtool.py> <images-del-respaldo> <dtbo-del-proveedor> stock/kernel-provider-reference.json <informe-nuevo.json>
```

El parser AVB utilizado corresponde al hash registrado en el informe y en
`stock/build-interface-reference.json`. La herramienta descubre el footer en
cada entrada, valida límites, descriptores y hashes; no usa offsets del NX789J.
Rechaza candidatos ambiguos y datos no nulos sin explicar. No extrae imágenes.
Los informes anteriores que referencian el hash antiguo de boot-audit.json se
conservan como evidencia histórica de sus respectivas revisiones Git.
