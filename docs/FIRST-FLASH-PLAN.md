# Plan de primer flasheo (NX733J) — v2 sin fastboot

Estado: 2026-09-30 (v2). **NADA se ha flasheado.** El fastboot del equipo está
capado incluso con bootloader desbloqueado (experiencia del usuario); el
flasheo va por **EDL 9008** (probado por el usuario con init_boot_b + Magisk) y
**TWRP** (build propio del usuario, arranca y flashea IMG físicas).

## Capacidades verificadas / por verificar

| Capacidad | Estado | Evidencia |
| --- | --- | --- |
| Escribir particiones por EDL 9008 | ✅ PROBADO | init_boot_b parcheado por Magisk, flasheado y arranca |
| AVB relajado con unlock | ✅ PROBADO | el init_boot modificado (hash AVB roto) arranca |
| TWRP arranca (touch/ADB/FBE PIN) | ✅ PROBADO | README TWRP, build b8.1-52997c9 |
| TWRP flashea IMG a físicas A/B explícitas | ✅ PROBADO | instaló recovery.img → recovery_b (/dev/block/sde60); twrp.flags tiene Boot-A/Boot-B/... |
| TWRP flashea IMG a lógicas (slot seleccionado) | ⚠️ PARCHEADO, SIN VALIDAR | parche logical-image-flash + preflights; README: "falta compilación y validación" |
| TWRP → vbmeta | ❌ NO | twrp.flags: `/vbmeta* flashimg=0` |
| TWRP fastbootd | ⚠️ INCLUIDO, SIN PROBAR | `TW_INCLUDE_FASTBOOTD`, README pendiente |
| Sideload con Lineage recovery nuestro | ⚠️ SIN VALIDAR | recovery recién construido, nunca arrancado |
| Restauración EDL del backup | ⚠️ NUNCA ejecutada (solo dump) | `stock/edl-audit-2026-09-23/` |

## Regla de oro del layout

`vbmeta_a`/`vbmeta_system_a` **SON OBLIGATORIOS** para arrancar nuestra ROM:
el fstab (que ya va en el vendor_boot) usa `avb=vbmeta_system`/`avb=vbmeta`;
init valida `system_a` etc. contra `vbmeta_system_a`, y este contra el
`vbmeta_a` raíz. Si quedan los stock (claves OEM), la cadena falla y las
particiones no montan → bootloop. Como TWRP no puede flashear vbmeta, **esa
escritura va por EDL** (2 particiones diminutas).

## Ruta B (recomendada por el usuario): "a la antigua" — TWRP + EDL mínimo

Mantiene intacto el stock B (activo) como fallback.

1. **Backup fresco** del estado actual por EDL (dump de `super`, `boot_b`,
   `init_boot_b`, `vbmeta_b`, `vbmeta_system_b`, `recovery_b`, etc.).
2. Copiar al teléfono las imágenes del slot A (del build final):
   `boot.img init_boot.img vendor_boot.img dtbo.img recovery.img` +
   `system.img system_ext.img product.img vendor.img odm.img
   vendor_dlkm.img system_dlkm.img`.
3. **En TWRP** (slot seleccionado = A):
   - Install Image → `boot.img` → destino **Boot-A**; ídem Init-Boot-A,
     Vendor-Boot-A, DTBO-A, Recovery-A.
   - Lógicas EROFS: `system.img` → System (slot A), etc. (flujo parcheado con
     preflight; snapshots deben estar vacíos — hoy lo están, update_engine
     IDLE).
   - `vendor/odm/vendor_dlkm/system_dlkm` son las preservadas stock (mismos
     bytes que el slot A ya tiene): opcional reescribirlas.
4. **EDL 9008**: escribir `vbmeta_a` y `vbmeta_system_a` nuestros (solo esas
   dos; el resto no se toca).
5. **Seleccionar slot A** (menú de TWRP con IBootControl, o desde el stock
   rooteado `bootctl set-active-slot a`) y reboot.
6. **Rollback**: `bootctl set-active-slot b` (B stock intacto), o retry
   automático del bootloader; rescate final EDL.

Riesgos: el flasheo de lógicas TWRP aún no está validado (probar primero con
UNA lógica, p.ej. system_ext, y verificar el log); el orden 4↔5 debe dejar
vbmeta escritas antes del primer arranque de A.

## Ruta A: sideload con Lineage recovery (nativa)

1. EDL: escribir nuestro `recovery.img` en `recovery_b` (1 partición).
2. Desde stock rooteado: `adb reboot recovery` → nuestro recovery (slot B
   activo).
3. `adb sideload lineage-23.2-...-nx733j.zip` → update_engine escribe TODO el
   slot A (físicas+lógicas, VABC correcto) y marca A activo.
4. Rollback idéntico (B intacto). Requisitos: recovery arranca y acepta la
   firma test-keys; sin validar aún.

## Ruta C: EDL total

Escribir todas las físicas A por EDL + construir un `super.img` completo
(nuestras lógicas A + stock B) con geometría del audit
(`stock/edl-audit-2026-09-23/super-metadata-audit.json`). Más trabajo y más
escritura; reservada como fallback de B y C.

## Prerequisitos go/no-go (v2)

1. Backup fresco del estado actual + backup de mayo intacto.
2. Material EDL (loader/rawprogram/patch) disponible y probado (ya lo está).
3. Decidir ruta (B por defecto) y hacer el **ensayo EDL** de restauración o
   aceptar conscientemente el riesgo.
4. Confirmar estado "snapshots vacíos" en el momento del flasheo.
