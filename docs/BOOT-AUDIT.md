# Auditoría de arranque NX733J — 2026-09-15

Estado: auditoría de imágenes completa para esta captura; **árbol ROM aún no compilable**.
No se cambió el teléfono ni TWRP. No se creó BoardConfigBringup.mk ni se inició Actions.

## Procedencia y alcance

Se leyeron boot, init_boot, vendor_boot, dtbo, vbmeta y vbmeta_system del slot B
del Android instalado. Cada transferencia coincidió en tamaño y SHA-256 con el
bloque leído desde el teléfono. Es un sistema con root: no es un paquete OEM
autenticado. Los valores de propiedades green/locked no se toman como prueba
independiente del estado del bootloader.

Evidencias fuera del árbol: diagnostics/rom-boot-audit/installed en el workspace.
Incluye imágenes, encabezados obtenidos con unpack_bootimg.py de AOSP, salida de
avbtool info_image, captura de propiedades seleccionadas e inventario del ramdisk.
Los scripts locales capture.py, unpack.py, check-descriptors.py e inspect-ramdisk.py
registran el procedimiento. No ejecutar de nuevo sobre los mismos archivos:
varios rechazan sobrescrituras y usan rutas locales.

stock/boot-audit.json registra tamaños, hashes y hechos resumidos. Los archivos
stock/ son evidencia: no se copian automáticamente al producto ni sustituyen la
configuración de SELinux/init que debe integrarse con LineageOS.

## Estructura verificada

| Componente | Observación | Consecuencia para el árbol |
| --- | --- | --- |
| boot | Header v4; kernel 36596224 bytes; sin ramdisk; Image ARM64 sin compresión | Separar kernel del ramdisk genérico |
| init_boot | Header v4; kernel vacío; ramdisk LZ4 legacy de 2236037 bytes | Generar ramdisk genérico limpio; no reutilizar el capturado como stock |
| vendor_boot | Header v4; páginas 4096; un fragmento PLATFORM sin nombre | Conservar distribución y cargas tempranas al integrar |
| DTB | 4487979 bytes dentro de vendor_boot | No sustituir por DTB de otro SM8750 |
| DTBO | 37 entradas; 14124069 bytes utilizados | Auditar selección de variantes; no elegir arbitrariamente una entrada |
| Bootconfig | 232 bytes; USB a600000.dwc3 y módulos en paralelo | Referencia OEM, separada de parámetros aportados por bootloader |
| Vendor ramdisk | 306 módulos; lista normal 106 entradas; recovery 303 | No usar la lista de recovery como lista del arranque normal |

Los tamaños de partición coinciden con BoardConfig existente. El campo os_version
del encabezado boot/init_boot está en cero; no inventar una fecha para sustituirlo.
Las propiedades AVB contienen versiones/fechas por componente que pueden diferir
del sistema Android 16.

La lista de system_dlkm/modules.load realmente tiene tamaño cero (confirmado con
root), aunque la partición contiene módulos. No significa que no existan módulos
system_dlkm ni justifica cargarlos todos.

## AVB: cadena y comprobaciones

- vbmeta encadena boot (rollback location 3), recovery (1) y vbmeta_system (2).
- vbmeta contiene hashes de dtbo, init_boot y vendor_boot; hashtrees de odm,
  system_dlkm, vendor y vendor_dlkm.
- vbmeta_system describe product, system y system_ext, además de un hash de pvmfw.
  El alcance OTA preliminar del árbol no resuelve todavía pvmfw.
- Se recomputó SHA-256(salt + bytes descritos): boot coincide con su descriptor;
  dtbo y vendor_boot coinciden con los de vbmeta.
- **init_boot B no coincide** con el descriptor de vbmeta. Una captura adicional
  de init_boot A tampoco coincide con el descriptor del slot B. No asumir que A
  corresponde a la misma versión o que es una alternativa limpia.
- dtbo no tiene footer AVB propio; su hash está en vbmeta. El fallo de info_image
  sobre dtbo por sí solo no indica que la partición esté dañada.
- No se verificaron firmas contra una clave OEM confiable ni aceptación de rollback
  por el bootloader. Coincidir con un descriptor no autentica el paquete completo.

No copiar firmas, salts o índices de rollback stock a una ROM por ensayo. Definir
qué imágenes genera LineageOS, cuáles se conservan y las claves/cadenas de desarrollo
antes de producir una OTA. No desactivar AVB como sustituto de esa decisión.

## Kernel y módulos

Kernel capturado: 6.6.92-android15-8-g3637f4904cf5-ab13944661-4k.
Los 306 módulos del vendor ramdisk llevan vermagic
6.6.30-android15-8-maybe-dirty-4k SMP preempt mod_unload modversions aarch64.

Esto corrige el supuesto previo de exigir el mismo número de parche. La
compatibilidad se debe resolver con KMI, símbolos/CRC, configuración y evidencias
de carga; ni el número diferente prueba incompatibilidad ni arrancar stock demuestra
que una recompilación OEM 6.6.30 vaya a funcionar. No recompilar ni sustituir módulos
todavía. Mantener el conjunto observado como referencia del primer arranque.

## Decisiones y próximos pasos

1. Primera ROM: conservar como referencia kernel/DTB/módulos del conjunto observado.
   Auditar KMI antes de integrarlos como prebuilts. Las fuentes OEM 6.6.30 quedan como
   material de investigación, no como reemplazo automático.
2. Construir init_boot genérico desde las fuentes de LineageOS; el capturado con
   hash distinto sirve para auditoría, no como prebuilt limpio. Obtener la versión
   stock limpia sigue siendo útil como referencia, pero no debe convertirse en un
   bloqueo artificial si se genera el ramdisk desde fuentes.
3. Preparar un dump reproducible de vendor/odm/system_ext/product de una versión
   coherente. Depurar la lista candidata por subsistema y resolver dependencias ELF.
   No convertir los 3718 candidatos directamente en módulos PRODUCT_PACKAGES.
4. Revisar VINTF/FCM/SELinux, servicios de primera etapa, cifrado y módulos contra
   la rama exacta LineageOS 23.2 antes de cerrar BoardConfigBringup.mk.
5. Definir pvmfw, AVB y alcance de actualización. Después ejecutar verificaciones
   de configuración y la primera compilación; aún no hay una ROM flasheable.

## Fuentes técnicas

- [AOSP: generic boot e init_boot](https://source.android.com/docs/core/architecture/partitions/generic-boot)
- [AOSP: formato vendor_boot v4](https://source.android.com/docs/core/architecture/partitions/vendor-boot-partitions)
- [AOSP: verificación de ABI/KMI](https://source.android.com/docs/core/architecture/kernel/abi-monitor)

Las mediciones y hashes de este informe proceden del dispositivo y de las imágenes
capturadas; las páginas anteriores explican los formatos y la metodología.
