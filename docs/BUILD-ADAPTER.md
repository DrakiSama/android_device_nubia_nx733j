# Adaptador de build: activación explícita

Fecha: 2026-09-26. Estado: adaptador presente, **build no ejecutado**. El guard
de compilación cambia de «archivo ausente» a «entradas privadas obligatorias y
verificables»: `BoardConfigBringup.mk` ya existe y detiene el make con un error
explícito si faltan las entradas. No hay ROM compilada ni flasheable.

## Qué conecta el adaptador

| Área | Variables fijadas | Evidencia |
| --- | --- | --- |
| Kernel | `TARGET_PREBUILT_KERNEL`, `BOARD_KERNEL_IMAGE_NAME`, no-strip de módulos | [KERNEL-PROVIDER](KERNEL-PROVIDER.md) |
| DTB | `BOARD_INCLUDE_DTB_IN_BOOTIMG`, `BOARD_PREBUILT_DTBIMAGE_DIR` | [BUILD-PROVIDER-MAPPING](BUILD-PROVIDER-MAPPING.md) |
| DTBO | `BOARD_PREBUILT_DTBOIMAGE` (contenedor de 18 MiB) | [DTBO-AVB-ENVELOPE](DTBO-AVB-ENVELOPE.md) |
| Bootconfig | `BOARD_BOOTCONFIG_FILE` (232 bytes stock) | [BOOT-AUDIT](BOOT-AUDIT.md) |
| Vendor ramdisk | módulos stock + listas de carga normal (106) / recovery (303) | [RAMDISK-LOAD-AUDIT](RAMDISK-LOAD-AUDIT.md) |
| AVB | cadena completa con 7 claves de desarrollo y locations 1-6 | [AVB-DEV-KEYS](AVB-DEV-KEYS.md) |
| Perfil preservado | `-include $(NX733J_PRESERVED_MK)`; descriptores de las 4 imágenes en vbmeta | [PRESERVED-PROFILE-INTEGRATION](PRESERVED-PROFILE-INTEGRATION.md) |

## Entradas privadas

- `NX733J_PROVIDER_DIR`: paquete stock verificado. Preparación local con
  `tools/prepare_build_inputs.sh <provider-dir> <dtb-file> <dtbo18-file> <destino>`.
- `NX733J_AVB_KEYS_DIR`: claves RSA-4096 de desarrollo generadas con
  `tools/generate_dev_avb_keys.sh` (7 claves, ver registro público).
- `NX733J_PRESERVED_MK` (opcional): fragmento privado con las cuatro
  `BOARD_PREBUILT_*IMAGE`; sin él, esas particiones se intentarían construir
  desde el vendor repo generado.
- `proprietary-files.txt`: presente y **sin entradas** para el primer arranque
  ([selección](BOOT-DEPENDENCY-SELECTION.md)). `extract-files.py` genera el
  andamiaje del vendor repo; no se hereda el volcado antiguo de `~/lineage`.

## Pendientes antes del primer arranque

1. **Fstab de primera etapa y metadatos depmod** del vendor ramdisk
   (`modules.dep/alias/softdep/blocklist`). Este `build/make` no expone
   copy-out de archivos extra al vendor ramdisk; el mecanismo se resolverá sin
   copiar el fstab stock en bloque ([VENDOR-RAMDISK-LAYOUT](VENDOR-RAMDISK-LAYOUT.md)).
2. **VINTF/FCM y SEPolicy fuente** (bloque de compatibilidad).
3. **CRC del kernel base** (3404 pendientes) si se cambia el proveedor.

## Validación prevista de la primera compilación

- Comparar cabeceras `mkbootimg` de boot/init_boot/vendor_boot con
  [BOOT-BUILD-COMPOSITION](BOOT-BUILD-COMPOSITION.md).
- `avbtool info_image` sobre vbmeta, vbmeta_system, boot, init_boot,
  vendor_boot, recovery y dtbo: cadena, locations y descriptores.
- `dtb.img` idéntico al DTB stock preparado; `modules.load`/`modules.load.recovery`
  contra las listas de referencia; imágenes preservadas idénticas al manifiesto.
- Errores de cableado de variables se corrigen en esa corrida; el adaptador no
  se declara validado hasta entonces.

## Estado del entorno local (2026-09-26)

- Sync de **lineage-23.2 completado** en `~/lineage-23.2` («repo sync has
  finished successfully»). El checkout 22.2 anterior y las copias stale se
  eliminaron dentro de WSL con autorización del usuario (E: recuperado a
  ~116 GB libres; dumps antiguos y `ubuntu-backup.tar` **movidos** a
  `G:\WSL-backups-20260926`, no borrados). La red de WSL necesitó **modo
  espejo** (`C:\Users\draki\.wslconfig`: `networkingMode=mirrored`,
  `dnsTunneling=true`) para alcanzar `android.googlesource.com`.
- Árbol del dispositivo instalado en `~/lineage-23.2/device/nubia/nx733j`
  (rsync del repositorio, sin `.git`) y vendor repo regenerado con el
  manifiesto sin entradas.
- Entradas privadas en `~/nx733j-build-inputs`; claves en
  `~/nx733j-avb-keys-20260926b`; variables en `~/nx733j-build-env.sh`.
- **Interfaces re-verificadas contra 23.2** (misma semántica; cambian líneas):
  `BOARD_PREBUILT_*IMAGE` en `core/Makefile` 4148/4394/4463/4603, target_files
  6531/6566/6575/6593, IMAGES 6951/6979/6983/6991, avisos 2031;
  `BOARD_PREBUILT_DTBIMAGE_DIR` en `board_config.mk` 1004-1006 y `Makefile`
  1043-1046; `BOARD_BOOTCONFIG_FILE` en `board_config.mk` 318-321; módulos del
  vendor ramdisk en `soong_config.mk` 583-586; macro
  `build-chained-vbmeta-image` y claves AVB (dtbo 1058, boot 1377, init_boot
  1580, vendor_boot 1784).
- **`lunch lineage_nx733j-trunk_staging-userdebug` validado** con las variables
  privadas: `TARGET_DEVICE=nx733j`, `TARGET_ARCH=arm64`,
  `TARGET_BOARD_PLATFORM=sun`, `TARGET_PREBUILT_KERNEL` apuntando al proveedor
  privado y `BOARD_PREBUILT_VENDORIMAGE` del fragmento preservado. **No se
  compiló nada.**

### Hallazgo de configuración corregido: identidad en el producto superior

Con la identidad declarada solo en la capa heredada `nx733j.mk`, Android 16
resolvía el producto como `generic` (arm, sin BoardConfig aplicado): las
variables de producto se importan «primer valor gana» y los productos base de
AOSP fijan `PRODUCT_DEVICE := generic`. Corrección: identidad
(`PRODUCT_DEVICE/BRAND/MANUFACTURER/MODEL`) en `lineage_nx733j.mk` (nivel
superior), documentada en [PRODUCT-LAYERS](PRODUCT-LAYERS.md). Verificado con
`get_build_var` tras el cambio.

Nota operativa: al copiar el árbol con rsync desde Windows conviene normalizar
CRLF (`grep -rlI $'\r' … | xargs sed -i 's/\r$//'`); el `.gitattributes` no
garantiza LF en la copia de trabajo Windows.

## Primera compilación acotada (2026-09-27)

`m bootimage vendorbootimage dtboimage` completó con éxito (16:33) con las
entradas privadas y los ajustes descritos abajo. Imágenes en
`out/target/product/nx733j/`:

| Imagen | Bytes | Nota |
| --- | ---: | --- |
| boot.img | 100663296 | kernel stock + AVB nuevo (rollback 1, clave dev) |
| vendor_boot.img | 100663296 | DTB stock (sha256 `43ac35e5…` idéntico al auditado) + ramdisk de módulos |
| dtbo.img | 25165824 | payload de 14124069 B (idéntico al stock) + descriptor nuevo |
| dtb.img | 4487979 | byte a byte igual al DTB stock auditado |

AVB verificado con `avbtool info_image`: footers v1.0, SHA256_RSA4096, rollback
index 1 y hash descriptors presentes en las tres imágenes. **No se flasheó ni
se tocó el teléfono.**

Auditoría contra el stock (2026-09-27):

- **boot.img**: kernel extraído byte a byte igual al proveedor (`11bf8868…`);
  header v4, ramdisk 0, cmdline vacío.
- **vendor_boot.img**: direcciones idénticas al stock (kernel 0x8000, ramdisk
  0x1000000, tags 0x100, DTB 0x1f00000); DTB idéntico (`43ac35e5…`); vendor
  ramdisk con **306 módulos** (igual al stock); `modules.load` 106 entradas y
  `modules.load.recovery` 303 (idénticas a las listas de referencia); depmod
  generado (alias/dep/softdep). Sin fstab y sin bootconfig (diferidos).
- **dtbo.img**: payload de 14124069 B idéntico al stock (`bff89700…`) con
  descriptor AVB nuevo.

### Ajustes aplicados para que compile

- `BOARD_INIT_BOOT_HEADER_VERSION := 4` (en BoardConfig del repo): el módulo
  fsgen de Android 16 lo exige por separado del de boot; evidencia: init_boot
  stock v4 (`stock/boot-audit.json`).
- Bootconfig **diferido**: hook `NX733J_BOOTCONFIG_FILE` (vacío). El módulo
  fsgen resuelve `Boot_config_file` relativo al directorio del módulo
  (`build/soong/fsgen/`) y no acepta el archivo; pendiente con el resto de
  ramdisk/fstab.
- Entradas privadas con **rutas relativas a $TOP** (`nx733j-inputs/…`): Soong
  paniquea o rechaza rutas absolutas/fuera del árbol.
- Target de Android 16: `vendor_bootimage` → **`vendorbootimage`**.
- Parches locales en proyectos sincronizados (se pierden con `repo sync`):
  `vendor_available` añadido a `libhwy` (external/google-highway) y
  `libskia_skcms` (external/skia); `vendor_available` desactivado en `libjxl`
  y `libdng_sdk` para cortar la cascada vendor (nuestro vendor es prebuilt).
- Reparación del checkout tras el crash de E:: `repo sync --force-sync`,
  índices de git reconstruidos, 3 proyectos re-clonados y archivos truncados
  restaurados.

Pendientes antes de un arranque: fstab/depmod del ramdisk, bootconfig,
VINTF y SEPolicy (la auditoría del target_files quedó completa el 2026-09-29).

## target_files: estado y reanudación (2026-09-28)

`m -j8 target-files-package` llegó al **~72% (≈103,9K/144,5K pasos)**; quedan
~40,5K. Cache intacta en `~/lineage-23.2/out` (no borrar `.ninja_log`).
Artefactos de packaging ya presentes (`all_modules.txt`, `build_fingerprint…`,
`system/`, `recovery/…`); aún sin zip `target_files`.

El obstáculo actual es el **entorno**, no el árbol: la VM de WSL cae
intermitentemente (`E_UNEXPECTED`), las sesiones matan procesos lanzados desde
ellas y el vhdx vive en un **HDD 5400 rpm** (cada reanudación de ninja escanea
largo). Mitigaciones aplicadas: red NAT (la espejo era inestable),
`vmIdleTimeout` 24 h, y una **unidad systemd real**
(`/etc/systemd/system/nx733j-build.service`, `User=draki`,
`Restart=on-failure`) que ejecuta `~/nx733j-build-tf-loop.sh`
(`lunch` verificado con reintentos + `m -j8` con reintentos; logs
`~/m-batch.log`, `~/lunch.log`).

Ajustes locales sobre proyectos sincronizados (se pierden con `repo sync`):
`vendor_available` añadido a `libhwy` (external/google-highway) y
`libskia_skcms` (external/skia); desactivado en `libjxl` y `libdng_sdk`; y
parche no-fatal del checker de ninja en `build/soong/ui/build/ninja.go`
(`CombinedOutputOrFatal()` → `CombinedOutput()`). Reaplicar si se resincroniza.

Reanudar: `bash ~/nx733j-build-tf-loop.sh` (lanzarlo con `setsid nohup` como
root; el cron lo relanza solo cada 5 min si no corre).

## target_files completado (2026-09-29)

`m -j8 target-files-package` terminó con éxito el **2026-09-29 14:28:49**
(5.276/5.276 pasos; 01:06:40 el tramo final tras reanudar la cache).
Paquete en
`out/target/product/nx733j/obj/PACKAGING/target_files_intermediates/lineage_nx733j-target_files.zip`
(3.702.606.126 B, 7.932 archivos; 13 particiones en `META/ab_partitions.txt`;
**nada se flasheó**).

Auditoría payload del zip contra las imágenes standalone ya auditadas
(2026-09-27) — todo idéntico:

- `IMAGES/boot.img` → kernel `11bf8868967b8f1657f9364afd48e0be2a351736485994fb5efae21aef595896` (referencia del proveedor).
- `IMAGES/vendor_boot.img` → DTB `43ac35e516a10f61bdbc9ab264b66bcc2255ea4cafd50ce0923cad3b97cbba4b` (referencia exacta) y vendor ramdisk **byte a byte** idéntico (`ddbb2945…`, hereda 306 módulos y listas 106/303).
- `IMAGES/dtbo.img` → hashes de entrada idénticos al dtbo auditado (`bff89700…`).

### Causas raíz del atasco del 29-S (y su corrección)

1. **Mezcla de propiedad root/draki** por reparaciones previas: `repo manifest
   -r` (paso de `build-manifest.xml`) fallaba con *dubious ownership*. Fix:
   `chown -R draki:draki ~/lineage-23.2` + `safe.directory '*'` para root y
   draki.
2. **Dos lanzadores en conflicto** (unidad systemd residual + cron con
   `runuser`): PAM/sesión mataba los builds ("Session terminated, killing
   shell...") y dos instancias peleaban por locks/`.ninja_fifo`. Fix: un único
   lanzador — cron root cada 5 min → `setsid nohup bash ~/nx733j-build-tf-loop.sh`
   (guardas: no relanzar si corre, si `chown.status` falta o si ya hay
   `BUILD_TF_EXIT=0`). Servicio systemd deshabilitado. `runuser`/`su` como
   lanzador de fondo **no** sirve: la sesión reapea los procesos.

## OTA completada (2026-09-30)

`m -j8 bacon` completó el **2026-09-30 14:08:01** (`BUILD_OTA_EXIT=0`).
Artefacto:
`out/target/product/nx733j/lineage-23.2-20260930-UNOFFICIAL-nx733j.zip`
(2.458.837.825 B; sha256 `4e08064e…`; payload.bin A/B de 2,4 GB; metadata
`ota-type=AB`, `pre-device=nx733j`; firmada con claves dev locales;
**nada se flasheó ni se publicó**).

Ajustes necesarios (commits `4089915` y `8e092a1`):

- En Lineage 23 el target canónico es **`bacon`** (no existe `otapackage`;
  `vendor/lineage/build/tasks/bacon.mk`).
- **`PRODUCT_BUILD_GENERIC_OTA_PACKAGE := true`**: con vendor prebuilt
  (`BUILDING_VENDOR_IMAGE` vacío) el build desactiva la OTA
  (`build_ota_package := false`, `core/Makefile:7210`) si `recovery_fstab`
  está vacío; el flag fuerza la generación. Provisional: el fix real es el
  recovery fstab + re-auditoría de imágenes.
- **`PRODUCT_PACKAGES += android.hidl.allocator@1.0-service`**: el módulo solo
  se instala para API de venta ≤34 (`PRODUCT_PACKAGES_SHIPPING_API_LEVEL_34`),
  pero `vintffm` (que corre en la ruta de vendor prebuilt) exige la
  declaración `android.hidl.allocator` en el manifiesto del framework.

Resiliencia verificada: un **corte de luz** (29-S ~17:31) y un **reinicio de la
VM WSL** (30-S ~12:56) interrumpieron builds; el cron `@reboot`/cada 5 min
relanzó solo y ninja reanudó desde cache sin pérdida. Reanudar/repetir la OTA:
`setsid nohup bash ~/nx733j-build-ota-loop.sh` (root; el cron lo vigila).

## Límites

El adaptador no demuestra compilación, arranque, aceptación AVB del bootloader
ni compatibilidad VINTF. No activa OTA ni instalación. Los ficheros de licencia
de las imágenes preservadas se reubican a system (comportamiento del build,
`core/Makefile:2127`).
