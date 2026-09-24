# NX733J: estado del bring-up

Actualizado: 2026-09-23 (Chile). Base auditada: `0590ddd`.
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
| Kernel stock y módulos | PARTIAL | 681 archivos, 479 nombres; sin CRC importados contradictorios | vendor_boot, DLKM, vendor | Falta contrastar ABI con exportaciones del kernel |
| zram/zsmalloc cargados | CONFIRMED | Notas GNU de sysfs coinciden con variantes vendor_boot 6.6.30 | Arranque stock B, kernel 6.6.92 | Identidad de build; no hash completo de memoria; conservar ambas copias |
| Política de carga para la ROM | PARTIAL | Listas ramdisk y scripts stock observados | Captura stock | No trasladar la lista recovery al arranque normal |
| Merge de snapshots | UNKNOWN | Propiedades Virtual A/B; snapshotctl ausente | Teléfono | COW no acredita estado actual del merge |
| AVB/FEC/OTA del producto | UNKNOWN | Cadena stock documentada | Pendiente | No copiar rollback, firmas ni alcance OTA automáticamente |
| Producto genérico | PARTIAL | Scaffold actualmente Lineage | Repositorio | Separación del producto pendiente; no se modifican makefiles en esta actualización |
| Build mínimo | BLOCKED | BoardConfigBringup.mk sigue ausente | BoardConfig.mk | Resolver kernel, AVB, SEPolicy y HAL antes de habilitarlo |
| Recuperación tras fallo | UNKNOWN | Existe respaldo 9008 | Usuario | Vía de restauración aún no validada |

## Siguiente objetivo concreto

Definir el contrato del proveedor de kernel stock: entradas de boot/vendor_boot,
módulos por partición, listas de carga y dependencias; mantener separada la futura
alternativa desde fuentes. Conservar las variantes stock de zram/zsmalloc en sus
particiones originales. Antes de generar imágenes, cerrar ABI/exportaciones,
política AVB/OTA y una vía de recuperación comprobable.

Evidencia y límites: [auditoría del respaldo](EDL-BACKUP-AUDIT.md).
No se ha compilado ni flasheado una ROM durante esta auditoría.
