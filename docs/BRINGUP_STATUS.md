# NX733J: estado del bring-up

Actualizado: 2026-09-24 (Chile). Base inicial auditada: `0590ddd`; ampliada con la auditoría publicada en `3fbcb9c`.
Objetivo: una base NX733J reutilizable para AOSP y derivados; adaptación específica
a LineageOS después del cierre de particiones, arranque y kernel.

CONFIRMED significa evidencia directa dentro del alcance indicado; PARTIAL indica
validación incompleta; INFERRED es una inferencia; UNKNOWN carece de evidencia
suficiente; BLOCKED requiere resolver una dependencia antes de avanzar.

| Component | Status | Evidence | Source | Notes |
| --- | --- | --- | --- | --- |
| GPT y tamaños | CONFIRMED | CRC primario/backup; 115 entradas XML | Respaldo NX733J, seis LUN | Sectores físicos de 4096 bytes; sin offsets prestados |
| Super y particiones B | CONFIRMED | Geometría, seis metadatos y siete hashtrees | super del respaldo | Sectores liblp de 512 bytes; COW presentes |
| Boot chain | PARTIAL | Firmas internas y claves padre/hijo A/B | vbmeta, boot, recovery | Trust anchor OEM y aceptación de rollback pendientes |
| init_boot limpio de referencia | CONFIRMED | init guardado por Magisk idéntico al stock | Respaldo B y captura instalada | La imagen instalada está parcheada |
| Recovery separado | CONFIRMED | Header v4; kernel vacío; ramdisk propio | Respaldo A/B | No demuestra restauración disponible |
| Kernel stock y módulos | PARTIAL | 681 archivos; 1685 CRC entre módulos coinciden; 3404 CRC del kernel pendientes | vendor_boot, DLKM, vendor y kernel vivo | Faltan CRC del kernel base, namespaces, firmas y orden de carga |
| Contrato del proveedor kernel | PARTIAL | Contrato y paquete preparados; consumidores del build identificados | Stock y build local | Adaptador detenido por diferencias DTB/DTBO y política AVB pendiente |
| Entrada DTB y límite DTBO | PARTIAL | Copia DTB íntegra; 37 entradas DTBO acotadas | Paquete stock y descriptor ya verificado | Cola DTBO con 234 bytes no nulos: identificar antes de recortar o integrar |
| Paquete privado stock | CONFIRMED | 715 copias verificadas; 681 módulos y 5 artefactos coinciden con manifiesto | Capturas stock locales | Preparado, sin integrar al build ni publicar binarios |
| zram/zsmalloc cargados | CONFIRMED | Notas GNU de sysfs coinciden con variantes vendor_boot 6.6.30 | Arranque stock B, kernel 6.6.92 | Identidad de build; no hash completo de memoria; conservar ambas copias |
| Política de carga para la ROM | PARTIAL | Cierre duro+soft de 106 módulos, grafo sin ciclos, 106 build IDs coincidentes | Ramdisk y teléfono stock | Falta secuencia efectiva y vinculación de aliases al hardware; recovery separado |
| Snapshots en la captura actual | CONFIRMED | Mapas linear/verity; 14 coinciden con backup; update_engine IDLE | Teléfono, 2026-09-24 | Sin snapshot activo observado; enum interno libsnapshot no consultado; conservar COW |
| AVB/FEC/OTA del producto | UNKNOWN | Cadena stock documentada | Pendiente | No copiar rollback, firmas ni alcance OTA automáticamente |
| Producto genérico | PARTIAL | Scaffold actualmente Lineage | Repositorio | Separación del producto pendiente; no se modifican makefiles en esta actualización |
| Build mínimo | BLOCKED | BoardConfigBringup.mk sigue ausente | BoardConfig.mk | Resolver kernel, AVB, SEPolicy y HAL antes de habilitarlo |
| Recuperación tras fallo | UNKNOWN | Existe respaldo 9008 | Usuario | Vía de restauración aún no validada |

## Siguiente objetivo concreto

El [contrato del proveedor](KERNEL-PROVIDER.md) y su manifiesto de referencia
identifican las entradas, hashes y responsabilidades. Siguiente: localizar evidencia
de valores CRC/exportaciones del kernel exacto (por ejemplo, Module.symvers de esa
compilación). Softdeps y grafo normal ya contrastados; la secuencia efectiva
y los aliases frente al hardware siguen pendientes. La captura de snapshots
y update_engine ya está documentada; el paquete privado stock quedó preparado.
La revisión de variables detectó diferencias de DTB/DTBO; se detuvo la activación
del adaptador. Siguiente decisión: empaquetado DTB/DTBO y política AVB antes de
conectar el proveedor, manteniendo separados plataforma y producto ROM.
La frontera estática del ramdisk normal ya está comprobada. La coincidencia de
5089 nombres y 1685 CRC entre módulos no cierra ABI. Conservar ambas variantes stock de zram/zsmalloc por
partición. AVB/OTA y recuperación siguen pendientes antes de generar imágenes.

Evidencia y límites: [auditoría del respaldo](EDL-BACKUP-AUDIT.md).
No se ha compilado ni flasheado una ROM durante esta auditoría.

Detalle y procedimiento: [CRC entre módulos](MODULE-EXPORT-CRC.md).

Última evidencia de carga: [ramdisk normal](RAMDISK-LOAD-AUDIT.md).

Estado de particiones en vivo: [snapshots y mapas](SNAPSHOT-STATE.md).

Entradas locales preparadas: [paquete del proveedor](KERNEL-PROVIDER-PACKAGE.md).

Bloqueos de integración precisos: [mapeo al build](BUILD-PROVIDER-MAPPING.md).

Próximo paso inmediato: identificar los 234 bytes no nulos posteriores al tamaño
DTBO protegido y contrastarlos con el respaldo 9008. Entrada DTB privada ya
preparada; DTBO y adaptador permanecen sin activar.
