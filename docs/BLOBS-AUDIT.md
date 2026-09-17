# Auditoría de blobs NX733J — 2026-09-15

Estado: clasificación reproducible de la lista candidata completa.
**Dump de vendor/odm capturado el 2026-09-17 (evidencia fuera del repo:
`diagnostics/vendor-odm-dump/`, hashes verificados); extracción EROFS y
dependencias ELF aún sin resolver, árbol no compilable.**

## Método y verificación

- `tools/review_candidates.py` valida el formato (0 duplicados, 0 rutas
  absolutas, 0 anomalías de espacios en 3718 entradas), clasifica por
  partición/categoría y asigna veredicto. Es determinista: dos ejecuciones
  consecutivas producen salidas byte-idénticas (verificado con SHA-256).
- `tools/elf_deps.py` es un parser ELF64 puro (DT_NEEDED/DT_SONAME) sin
  dependencias externas. `--selftest` construye un ELF sintético y valida el
  parseo; un escaneo real de `diagnostics/` encontró 1 ELF (objeto BPF) y lo
  procesó sin errores. Omite placeholders de nube y archivos ilegibles.
- Salidas: `stock/candidates-report.json` (máquina) y
  `stock/proprietary-files.draft.txt` (borrador con marcas `# review`).

## Resultados (3718 entradas)

| Veredicto | Entradas | Significado |
| --- | --- | --- |
| extract | 2928 | Candidatos a blob: elf-lib 1555, elf-bin 314, firmware 385, config-xml 221, config-json 151, config-text 116, init-rc 157, calibration 28, kernel-module 1 |
| review | 645 | Decisión caso por caso: overlay 219, media 242, other 176, apk 6, apex 2 |
| port-to-source | 145 | No extraer: vintf 114, build-generated 19, sepolicy-compiled 12 |

## Decisiones

- **No extraer como blobs**: `build.prop`, `fs_config_dirs/files`,
  `passwd`/`group`, `NOTICE.xml.gz`, `ueventd.rc` y `precompiled_sepolicy*`
  los genera el build desde fuente. Los manifests VINTF van en el device tree
  (las 127 declaraciones ya están en `stock/hal-inventory.json`). La sepolicy
  compilada se sustituye por SEPolicy fuente, no se copia.
- **Anomalías verificadas contra el dispositivo (2026-09-17, slot B, root)**:
  `vendor/build.prop` es archivo regular de 39126 bytes (no artefacto de
  symlink; sigue siendo port-to-source); `vendor/ifas.ko` es archivo regular
  de 1096120 bytes en raíz de vendor (módulo real); `/vendor/odm_dlkm/` es un
  directorio real dentro de vendor que solo contiene `etc/build.prop`, y
  `/vendor/odm` es un symlink a `/odm`. El odm real (892928 bytes) solo trae
  `etc/` con configs, VINTF y sepolicy precompilada: sin blobs relevantes.
- El borrador `stock/proprietary-files.draft.txt` **no se promueve** a
  `proprietary-files.txt` hasta cerrar los pendientes de abajo.
- Las listas stock siguen siendo evidencia; nada de esto instala archivos en
  el producto ni desbloquea `BoardConfigBringup.mk`.

## Pendientes que bloquean extracción y compilación

1. ~~Dump reproducible de vendor/odm~~ **hecho el 2026-09-17** (slot B, misma
   versión auditada; tamaños coinciden con lpdump y SHA-256 verificado en
   ambos extremos; ver `diagnostics/vendor-odm-dump/manifest.json`). Queda:
   extraer el EROFS (WSL), ejecutar `tools/elf_deps.py` sobre el árbol
   extraído y resolver cada dependencia faltante como proveída por
   AOSP/LineageOS o como blob adicional. El dump de system_ext/product sigue
   pendiente de autorización expresa.
2. Inventario de system_ext/product: la lista candidata no tiene entradas de
   esas particiones todavía.
3. Decidir APK (6), APEX (2), overlays (219) y media (242): prebuilt vs fuente
   y licencias. Los overlays ZTE podrían no ser necesarios en LineageOS.
4. Revisar los 176 `other` (`.fs`, `.dat`, `.eai`, datos sin extensión, etc.).
5. Auditoría KMI de kernel/módulos (ver `docs/BOOT-AUDIT.md`) antes de
   integrar cualquier prebuilt de kernel.
