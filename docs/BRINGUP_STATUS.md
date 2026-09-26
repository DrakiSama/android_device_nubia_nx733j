# NX733J: estado del bring-up

Actualizado: 2026-09-26 (Chile). Objetivo: base reutilizable AOSP, kernel stock
inicial sustituible; adaptación específica a una ROM después del cierre de la base.

CONFIRMED se limita a la evidencia indicada. PARTIAL implica trabajo pendiente;
INFERRED es una deducción, UNKNOWN falta de evidencia y BLOCKED una dependencia
que impide habilitar el siguiente paso.

| Component | Status | Evidence | Source | Notes |
| --- | --- | --- | --- | --- |
| GPT y tamaños | CONFIRMED | Seis LUN, CRC y 115 entradas XML | Respaldo 9008 | Sin offsets prestados |
| Super / particiones B | CONFIRMED | Seis metadatos y siete hashtrees | Respaldo y capturas | FEC no comprobado; conservar COW |
| Filesystems lógicos | CONFIRMED | Siete EROFS; metadata F2FS | Super, fstab, montajes vivos | Tipos system/product/system_ext completados; tamaños ROM aún desconocidos |
| Cadena AVB stock | PARTIAL | Firmas internas, claves padre/hijo, payloads | Imágenes A/B | Falta aceptación OEM y rollback |
| DTB / DTBO | CONFIRMED | DTB íntegro; contenedor DTBO interno A/B de 18 MiB | Respaldo y proveedor | Entradas privadas preparadas; partición DTBO sigue siendo 24 MiB |
| pvmfw | PARTIAL | Header v3, 1 MiB; hashes A/B distintos y válidos | Respaldo, GPT, teléfono | Resolver descriptor y firmware por slot en política OTA |
| init_boot limpio | CONFIRMED | Init original guardado por Magisk igual al stock | Respaldo B y captura | Init ROM se reconstruirá; no reutilizar el parcheado |
| Recovery separado | CONFIRMED | Header v4, kernel vacío, ramdisk propio | Respaldo | No prueba disponibilidad de restauración |
| Argumentos de boot | PARTIAL | v4 explícito en ambas listas; direcciones stock | Cabeceras y mkbootimg local | Corregidos en BoardConfig; no compilado |
| Kernel / módulos | PARTIAL | 681 archivos; 1685 CRC entre módulos coinciden | Stock y exports vivos | 3404 CRC del kernel base, namespaces y firmas pendientes |
| zram / zsmalloc | CONFIRMED | Build IDs vivos corresponden a vendor_boot 6.6.30 | Kernel stock 6.6.92 | Conservar variantes por partición; no certifica otra ABI |
| Carga temprana | PARTIAL | 106 build IDs; cierre duro/soft sin ciclos | Ramdisk y sysfs | Secuencia efectiva y aliases al hardware pendientes |
| Contenido vendor ramdisk | CONFIRMED | 306 módulos, 7 archivos auxiliares, 3 directorios; modos/uid/gid | CPIO stock | No contiene init OEM; etiquetas SELinux aún no derivadas |
| Fstab ROM | PARTIAL | 25 entradas, 14 tempranas; semántica emmc/formattable revisada | Stock y código init/fs_mgr | Sigue como referencia; no instalado en producto |
| Proveedor kernel | PARTIAL | 715 payloads privados comprobados; contrato definido | Capturas stock | Falta adaptador consumido por el build |
| Snapshots observados | CONFIRMED | Mapas linear/verity, 14 extents coincidentes, update_engine IDLE | Captura del teléfono | Observación temporal, no garantía para una OTA futura |
| Perfil de construcción | PARTIAL | Productores y prebuilts definidos en contrato stock B | Decisión de ingeniería | No activado; [diseño de integración verificado](PRESERVED-PROFILE-INTEGRATION.md) (interfaces y checkout); adaptador, modo del generador y AVB/claves pendientes |
| AVB / OTA ROM | UNKNOWN | Cadena e interfaces stock documentadas | Pendiente | Perfil inicial sin OTA; claves, rollback y aceptación aún abiertos |
| Referencias de init conservado | PARTIAL | 154 rc, 28 declaraciones externas, estados/rutas consultados | Vendor stock y ADB | 87 acciones OEM clasificadas; RNDIS explicado; visibilidad shell/root corregida; superposición USB pendiente |
| Producto genérico | PARTIAL | Capa genérica e identidad separadas; entrada Lineage conservada | Repo | nx733j.mk separado del wrapper Lineage; ningún nuevo producto compilado |
| Build mínimo | BLOCKED | BoardConfigBringup.mk ausente deliberadamente | BoardConfig | Kernel, ramdisk, AVB, vendor, VINTF y SELinux incompletos |
| Recuperación tras fallo | UNKNOWN | Existe respaldo 9008 | Usuario | Restauración no validada; fastboot no asumido funcional |

## Siguiente objetivo concreto

El [perfil inicial](BUILD-PROFILE.md) define qué se reconstruye y qué se conserva.
Imágenes completas vendor/odm/DLKM contrastadas con super y descriptores AVB.
Las acciones de init.vendor.rc quedaron clasificadas: no se añadirá un import
global ni concat_props_zte al init ROM. La propiedad de nombre USB ya existe
en vendor/build.prop. La revisión USB encontró acciones OEM/ROM superpuestas y
la rama OEM que explica RNDIS. La captura root corrige los vacíos de shell. Siguiente:
integrar explícitamente el perfil de imágenes preservadas con producto/proveedor antes de habilitar
prebuilts, ramdisk y AVB. Los dos rc USB del sistema coinciden con ROM; vendor
ya define el montaje FunctionFS; adbd ROM y su acceso SELinux básico están trazados. La superposición no prueba un defecto del port. Véase [frontera USB](USB-INIT-BOUNDARY.md).
La identidad diferente de pvmfw A/B impide tratar ambos slots como firmware
intercambiable. Las claves y firmware OEM no se heredan como política de firma ROM.

Antes de habilitar imágenes también faltan las dependencias mínimas vendor,
VINTF y SELinux. La verificación de ABI completa del kernel sigue abierta; no
se repiten intentos fallidos contra artefactos GKI públicos sin una fuente nueva.
No se ha compilado ni arrancado una ROM propia, ni ejecutado flasheos o formatos.

## Evidencia y procedimientos

- [Respaldo y particiones](EDL-BACKUP-AUDIT.md), [snapshots](SNAPSHOT-STATE.md).
- [Corrección DTBO](DTBO-AVB-ENVELOPE.md), [pvmfw y AVB](PVMFW-AVB-SCOPE.md).
- [Composición del build](BOOT-BUILD-COMPOSITION.md), [interfaces del proveedor](BUILD-PROVIDER-MAPPING.md).
- [Contrato kernel](KERNEL-PROVIDER.md), [paquete privado](KERNEL-PROVIDER-PACKAGE.md).
- [Contenido ramdisk / fstab](VENDOR-RAMDISK-LAYOUT.md), [carga normal](RAMDISK-LOAD-AUDIT.md).
- [CRC entre módulos](MODULE-EXPORT-CRC.md), [auditoría boot histórica corregida](BOOT-AUDIT.md).

[Dependencias del vendor conservado](PRESERVED-VENDOR-DEPENDENCIES.md) y
[capas de producto](PRODUCT-LAYERS.md).

[Decisiones de port de init OEM](OEM-INIT-PORT-DECISIONS.md).

[Contrato ADB del producto](ADB-PRODUCT-CONTRACT.md): provisión, backend y
permisos de ffs.ready trazados; orden efectivo y política combinada pendientes.

[Entradas de imágenes preservadas](PRESERVED-IMAGE-INPUTS.md): cuatro imágenes
revalidadas y fragmento privado preparado; sin inclusión automática en BoardConfig.
[Integración del perfil preservado](PRESERVED-PROFILE-INTEGRATION.md): diseño
verificado contra el checkout (interfaces, target_files/OTA) y hallazgo de la
extracción antigua no auditada en `~/lineage`.
[Selección mínima de dependencias](BOOT-DEPENDENCY-SELECTION.md): 28 referencias
externas de init clasificadas; cero blobs OEM requeridos para el primer arranque
con ADB.

[Separación de inventarios](PROFILE-BLOB-SCOPE.md): 3718 entradas vendor/odm ya
cubiertas por prebuilts; 2621 system_ext/product pendientes de selección.

`/system/bin/usbconfig` quedó resuelto por análisis estático: es un helper de
modo fábrica (lee android_usb/android0/manu_tag; publica
`sys.usb.config=diag,adb,facmode` y `sys.usb.factory`) y en el kernel actual el
nodo no existe, por lo que es inoperante en consumidor. Decisión propuesta:
excluirlo del system reconstruido sin sustituto. Véase
[análisis de usbconfig](USBCONFIG-ANALYSIS.md). El
[diseño de integración del perfil preservado](PRESERVED-PROFILE-INTEGRATION.md)
quedó verificado contra el checkout (interfaces `BOARD_PREBUILT_*`, target_files
y OTA) y detectó una extracción antigua sin auditar en `~/lineage` que no debe
usarse como fuente. La [selección mínima de dependencias](BOOT-DEPENDENCY-SELECTION.md)
concluyó que el primer arranque con ADB no requiere ningún blob OEM externo en
las particiones reconstruidas: el generador acotado puede arrancar vacío y
crecer por subsistema. Siguiente objetivo: adaptador de build revisado con
política de claves/fstab/bootconfig y activación explícita del fragmento
privado.
