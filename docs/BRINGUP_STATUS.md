# NX733J: estado del bring-up

**Revisado: 2026-10-23.** Git estaba en `4eb973d` y sincronizado con
`origin/lineage-23.2`. Los últimos artefactos de ROM documentados corresponden
al 2026-09-30. WSL no respondió durante esta revisión, así que esos artefactos
no se volvieron a inspeccionar.

Los estados de esta tabla distinguen configuración, validación offline y prueba
en dispositivo. `CONFIRMADO` siempre queda limitado a la evidencia citada;
`PARCIAL` señala trabajo pendiente; `DESCONOCIDO` significa que no hay evidencia.

| Área | Estado | Evidencia y límite |
| --- | --- | --- |
| Identidad / BoardConfig | CONFIRMADO | `lineage_nx733j.mk`, `BoardConfig.mk`; detalles de build en [BUILD-ADAPTER](BUILD-ADAPTER.md). |
| Kernel/DTB/DTBO iniciales | VALIDADO OFFLINE | El build del 2026-09-27 registró comparación de kernel, DTB y payload DTBO contra stock; no prueba arranque. |
| target_files | VALIDADO OFFLINE | Build y auditoría de payload registrados el 2026-09-29 en [BUILD-ADAPTER](BUILD-ADAPTER.md). |
| OTA | VALIDADO OFFLINE | OTA final registrada el 2026-09-30, SHA-256 `fdf7202e5d1d48ae039c7d0515c446a57caab82fd0a114f481273f81baee01d5`; no instalada. |
| VINTF / FCM | VALIDADO OFFLINE | Matriz de 126 HAL; `checkvintf --check-compat` registró `COMPATIBLE (rc=0)` contra vendor/odm stock. |
| Vendor ramdisk | VALIDADO OFFLINE | Fstab, blocklist, bootconfig y hashes de 306 módulos registrados en [auditoría del ramdisk](../stock/vendor-ramdisk-layout-audit.json). No prueba montaje ni carga en el teléfono. |
| SEPolicy fuente | PENDIENTE | Falta portar y validar la política fuente para el producto ROM. |
| ABI del kernel | PARCIAL | Hay análisis de módulos; CRC del kernel base, namespaces y condiciones de firma siguen sin cerrar si se cambia el proveedor. Véase [MODULE-EXPORT-CRC](MODULE-EXPORT-CRC.md). |
| AVB / pvmfw / release | PARCIAL | Se usaron claves de desarrollo y rollback 1 en imágenes registradas. Aceptación del bootloader, tratamiento de pvmfw y claves/rollback de release pendientes. |
| TWRP como ruta de instalación | PENDIENTE | El [plan de flasheo](FIRST-FLASH-PLAN.md) mantiene sin validar el manejo de vbmeta, particiones lógicas y cambio de slot requerido. |
| EDL y rescate | PARCIAL | Escritura de `init_boot_b` por EDL reportada por el usuario; restauración del backup/ensayo EDL no consta como ejecutado. |
| ROM en dispositivo | PENDIENTE | No hay evidencia de que esta ROM se haya flasheado o arrancado. |
| CI `repo-checks` | HISTÓRICO | La continuidad registra una ejecución verde en 2026-09-26/28; el estado para HEAD `4eb973d` no fue comprobado en esta revisión. |

## Hechos de plataforma útiles

- Nubia NX733J / PQ84A01, Qualcomm `sun` (SM8750); slot B fue observado en las
  capturas documentadas. Comprueba el slot actual antes de cualquier operación.
- Tamaños y particiones están en `stock/boot-audit.json` y documentos de
  auditoría. Hay siete particiones lógicas EROFS; no existe `odm_dlkm`.
- `pvmfw` A y B tienen identidades distintas; no son intercambiables. Véase
  [PVMFW-AVB-SCOPE](PVMFW-AVB-SCOPE.md).
- El árbol no debe confundirse con TWRP u OrangeFox. El estado del build no
  demuestra que la recuperación esté lista para instalarlo.

## Siguiente secuencia

1. Cerrar la documentación de SEPolicy, `pvmfw` y la política AVB/OTA de release.
2. Completar las validaciones de TWRP y el ensayo de restauración EDL del plan.
3. Cuando el usuario decida iniciar la prueba, revisar de nuevo los artefactos,
   prerequisitos y slot; después validar el arranque con evidencia fechada.

No declarar la ROM lista para flashear hasta completar los prerequisitos de la
ruta elegida. Los builds, VINTF y auditorías offline no equivalen a pruebas en
el dispositivo.

## Evidencia y procedimientos

- [Adaptador y builds](BUILD-ADAPTER.md), [plan de flasheo](FIRST-FLASH-PLAN.md).
- [Auditoría de arranque](BOOT-AUDIT.md), [composición de imágenes](BOOT-BUILD-COMPOSITION.md), [vendor ramdisk](VENDOR-RAMDISK-LAYOUT.md).
- [Kernel/CRC](KERNEL-AND-OEM-AUDIT.md), [VINTF y dependencias](BOOT-DEPENDENCY-SELECTION.md), [pvmfw](PVMFW-AVB-SCOPE.md).
- [Respaldo EDL](EDL-BACKUP-AUDIT.md), [perfil preservado](BUILD-PROFILE.md), [claves de desarrollo](AVB-DEV-KEYS.md).
