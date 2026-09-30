# Plan de primer flasheo (NX733J) — borrador operativo

Estado: 2026-09-30. **NADA se ha flasheado.** Este documento define el
procedimiento y sus prerequisitos; no autoriza escritura por sí solo.

## Principios de seguridad (no negociables)

1. **Nunca flashear firmware/bootloader** (xbl, abl, hyp, tz, devcfg, qupfw,
   etc.): esos son los únicos candidatos a brick real. Nuestro build no los
   incluye y este plan no los toca.
2. **Flashear solo el slot inactivo**; el slot activo (stock) queda de
   rollback inmediato (`fastboot --set-active=<slot>` y listo).
3. **No tocar userdata, metadata ni persist** sin decisión explícita aparte:
   userdata permanece cifrado stock (posible bootloop si algo falla, sin
   pérdida de datos); metadata contiene las claves FBE.
4. **Vía de rescate primero**: restaurar por EDL solo como último recurso y
   únicamente tras validar el material (ver "Ensayo EDL"). Si el EDL no está
   verificado, no se inicia el flasheo.
5. Cada paso con su comando de reversión documentado.

## Prerequisitos (go/no-go)

| # | Requisito | Estado | Cómo verificar |
| --- | --- | --- | --- |
| 1 | Backup EDL completo del stock (mayo) intacto | Auditado 2026-09-23 (GPT/super/AVB) | `stock/edl-audit-2026-09-23/`; verificar SHAs del material privado |
| 2 | Cargador firehose + rawprogram/patch XML disponibles | **POR CONFIRMAR (privado)** | El usuario indica la carpeta del dump de mayo |
| 3 | Vía de restauración EDL probada | **NO probada nunca** | Ensayo (abajo) o decisión consciente de aceptar el riesgo |
| 4 | Bootloader desbloqueado | Probable (stock con Magisk instalado) | `fastboot flashing get_unlock_ability` / arranque muestra aviso naranja |
| 5 | fastboot/fastbootd operativos en el PC | Por verificar | `fastboot devices`, `fastboot getvar current-slot` |
| 6 | Artefacto ROM completo y auditado | En curso (rebuild bacon) | `out/target/product/nx733j/*.img` + hashes |
| 7 | Plan de datos de usuario decidido (no se toca /data) | Por confirmar con el usuario | — |

## Material a flashear (del target_files/OTA)

| Partición | Imagen | Slot | Notas |
| --- | --- | --- | --- |
| boot | boot.img | inactivo | kernel stock, AVB dev |
| init_boot | init_boot.img | inactivo | ramdisk ROM (sin Magisk) |
| vendor_boot | vendor_boot.img | inactivo | DTB stock + fstab + módulos + bootconfig |
| dtbo | dtbo.img | inactivo | payload stock |
| recovery | recovery.img | inactivo | header v4, sin kernel |
| system/system_ext/product | system.img/product.img/system_ext.img | inactivo | fastbootd, particiones lógicas |
| vendor/odm/dlkm | imágenes preservadas | inactivo | bytes stock |
| vbmeta / vbmeta_system | vbmeta.img / vbmeta_system.img | inactivo | claves dev (rollback 1) |

## Secuencia propuesta (A/B, sin tocar /data)

1. **Preflight**: leer slots (`fastboot getvar current-slot`, `fastboot getvar
   slot-count`), confirmar inactivo (p.ej. `a` si activo es `b`), anotar
   `ro.boot.slot_suffix` en adb. Verificar batería >50%.
2. **Flashear al slot inactivo** (en fastboot/bootloader):
   `fastboot --slot <inactivo> flash boot/boot...` para boot, init_boot,
   vendor_boot, dtbo, recovery, vbmeta, vbmeta_system (avbtool verificado).
   Para super: preferir **fastbootd** (`fastboot reboot fastboot`) y
   `fastboot --slot <inactivo> flash system/system_ext/product ...`; el resto
   (vendor/odm/dlkm) ya son las imágenes stock preservadas (mismos bytes que el
   slot actual; se pueden dejar como están).
3. **Cambio de slot controlado**: `fastboot --set-active=<inactivo>` →
   reboot. Primer arranque lento (dex2oat).
4. **Si no arranca (bootloop)**:
   - 3-4 intentos/5 min → volver: `fastboot --set-active=<stock>` (recupera el
     sistema stock al instante; sin pérdida de datos).
   - Capturar evidencias del fallo (pantalla, `adb logcat` si llega,
     `last_kmg`? ver más abajo) antes de reintentar.
5. **Solo si el slot stock también se corrompiera** (no esperado en este
   plan): restauración EDL completa (material de mayo).

## Ensayo EDL (para convertir el "NO probado" en "verificado")

Opciones, de menor a mayor riesgo:
1. **Verificación estática** (sin escribir): recomputar SHA-256 del material
   (loader, rawprogram/patch, imágenes del dump) y contrastar con
   `stock/edl-audit-2026-09-23/evidence-index.json`. Confirmar que el PC
   detecta el teléfono en 9008 con el driver instalado (se puede ver el device
   sin escribir nada).
2. **Ensayo en lectura**: usar QFIL/fh_loader en modo "solo leer" (si el
   material lo permite) para verificar handshake y detección.
3. **Restauración de una partición inocua** (p.ej. re-flashear la MISMA
   dtbo_b stock por EDL) y verificar que arranca igual: esto SÍ escribe, y
   debe decidirlo el usuario.

Hasta completar al menos (1)+(2), el flasheo queda en espera.

## Contingencias documentadas

- Bootloader no acepta vbmeta dev (verificación estricta): reflashear
  `vbmeta` con `--disable-verity --disable-verification` (rebuild del vbmeta
  con flags) y reintentar. Última ratio: restaurar stock completo por EDL.
- fastbootd no soporta `--slot` para lógicas en este device: escribir primero
  el otro slot con set_active temporal, o usar update_engine desde el sistema
  stock con la OTA firmada (rechazada por claves stock, no viable), o flashear
  el super correspondiente (con metadatos del slot objetivo) por fastboot.
- El kernel/init stock del slot activo NO se modifica en ningún paso.

## Pendientes de este documento

- Confirmar carpeta y hashes del material EDL (usuario).
- Confirmar estado de desbloqueo (fastboot) y si hay `get_unlock_ability`.
- Decidir el "go" para el paso de ensayo (2)/(3).
- Agregar los comandos exactos por partición una vez decidido el artefacto
  final (tras el rebuild OTA con VINTF + ramdisk).
