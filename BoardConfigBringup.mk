# Adaptador de activación del build NX733J (revisado 2026-09-26).
# Documentación: docs/BUILD-ADAPTER.md. Evidencias: docs/KERNEL-PROVIDER.md,
# docs/AVB-DEV-KEYS.md, docs/PRESERVED-PROFILE-INTEGRATION.md.
#
# Entradas privadas obligatorias (fuera del repositorio; sin ellas el build se
# detiene con un error explícito en vez de producir una imagen accidental):
#   NX733J_PROVIDER_DIR  paquete stock verificado: kernel/Image, dtb/*.dtb,
#                        dtbo/dtbo.img (18 MiB), modules/vendor_boot/lib/modules,
#                        reference/bootconfig y listas de carga.
#   NX733J_AVB_KEYS_DIR  claves AVB de desarrollo (tools/generate_dev_avb_keys.sh).
# Entrada privada opcional:
#   NX733J_PRESERVED_MK  fragmento con BOARD_PREBUILT_*IMAGE (perfil preservado).

ifeq ($(strip $(NX733J_PROVIDER_DIR)),)
$(error NX733J_PROVIDER_DIR no está definido: apunta al paquete privado del proveedor stock)
endif
ifeq ($(strip $(NX733J_AVB_KEYS_DIR)),)
$(error NX733J_AVB_KEYS_DIR no está definido: genera claves con tools/generate_dev_avb_keys.sh)
endif

# --- Proveedor kernel stock (prebuilt, sustituible) ---
TARGET_PREBUILT_KERNEL := $(NX733J_PROVIDER_DIR)/kernel/Image
BOARD_KERNEL_IMAGE_NAME := Image
# Los módulos stock se conservan byte por byte (firmas y metadatos).
BOARD_DO_NOT_STRIP_VENDOR_MODULES := true
BOARD_DO_NOT_STRIP_VENDOR_RAMDISK_MODULES := true

# DTB NX733J: entrada .dtb única verificada; se empaqueta en vendor_boot.
BOARD_INCLUDE_DTB_IN_BOOTIMG := true
BOARD_PREBUILT_DTBIMAGE_DIR := $(NX733J_PROVIDER_DIR)/dtb

# DTBO: contenedor interno de 18 MiB con footer reconocible por avbtool; el
# descriptor se recalcula durante el empaquetado.
BOARD_PREBUILT_DTBOIMAGE := $(NX733J_PROVIDER_DIR)/dtbo/dtbo.img

# Bootconfig stock auditado (232 bytes); su alcance está documentado en
# docs/BOOT-AUDIT.md. No inventa parámetros: reproduce los observados.
BOARD_BOOTCONFIG_FILE := $(NX733J_PROVIDER_DIR)/reference/bootconfig

# --- Vendor ramdisk: módulos stock con listas separadas normal/recovery ---
# 306 módulos; listas de 106/303 entradas (docs/RAMDISK-LOAD-AUDIT.md).
BOARD_VENDOR_RAMDISK_KERNEL_MODULES := \
    $(wildcard $(NX733J_PROVIDER_DIR)/modules/vendor_boot/lib/modules/*.ko)
BOARD_VENDOR_RAMDISK_KERNEL_MODULES_LOAD := \
    $(shell cat $(NX733J_PROVIDER_DIR)/reference/modules.load.boot)
BOARD_VENDOR_RAMDISK_RECOVERY_KERNEL_MODULES_LOAD := \
    $(shell cat $(NX733J_PROVIDER_DIR)/reference/modules.load.recovery)
# PENDIENTE antes del primer arranque: metadatos depmod del ramdisk stock
# (modules.dep/alias/softdep/blocklist) y fstab de primera etapa. Este
# build/make no ofrece copy-out de archivos extra al vendor ramdisk; no se
# copia automáticamente el fstab stock (docs/VENDOR-RAMDISK-LAYOUT.md).

# --- AVB: cadena completa con claves de desarrollo explícitas ---
# Sin claves OEM ni test keys; política en docs/AVB-DEV-KEYS.md.
BOARD_AVB_ENABLE := true
BOARD_AVB_ALGORITHM := SHA256_RSA4096
BOARD_AVB_KEY_PATH := $(NX733J_AVB_KEYS_DIR)/root.pem
# Índice de rollback de desarrollo, fijo y explícito (no imita índices stock).
BOARD_AVB_ROLLBACK_INDEX := 1

# Particiones encadenadas hacia vbmeta raíz. Locations 1-3 reproducen el
# esquema stock; 4-6 son asignaciones de desarrollo para el resto.
BOARD_AVB_BOOT_KEY_PATH := $(NX733J_AVB_KEYS_DIR)/boot.pem
BOARD_AVB_BOOT_ALGORITHM := SHA256_RSA4096
BOARD_AVB_BOOT_ROLLBACK_INDEX := 1
BOARD_AVB_BOOT_ROLLBACK_INDEX_LOCATION := 3

BOARD_AVB_RECOVERY_KEY_PATH := $(NX733J_AVB_KEYS_DIR)/recovery.pem
BOARD_AVB_RECOVERY_ALGORITHM := SHA256_RSA4096
BOARD_AVB_RECOVERY_ROLLBACK_INDEX := 1
BOARD_AVB_RECOVERY_ROLLBACK_INDEX_LOCATION := 1

BOARD_AVB_INIT_BOOT_KEY_PATH := $(NX733J_AVB_KEYS_DIR)/init_boot.pem
BOARD_AVB_INIT_BOOT_ALGORITHM := SHA256_RSA4096
BOARD_AVB_INIT_BOOT_ROLLBACK_INDEX := 1
BOARD_AVB_INIT_BOOT_ROLLBACK_INDEX_LOCATION := 4

BOARD_AVB_VENDOR_BOOT_KEY_PATH := $(NX733J_AVB_KEYS_DIR)/vendor_boot.pem
BOARD_AVB_VENDOR_BOOT_ALGORITHM := SHA256_RSA4096
BOARD_AVB_VENDOR_BOOT_ROLLBACK_INDEX := 1
BOARD_AVB_VENDOR_BOOT_ROLLBACK_INDEX_LOCATION := 5

BOARD_AVB_DTBO_KEY_PATH := $(NX733J_AVB_KEYS_DIR)/dtbo.pem
BOARD_AVB_DTBO_ALGORITHM := SHA256_RSA4096
BOARD_AVB_DTBO_ROLLBACK_INDEX := 1
BOARD_AVB_DTBO_ROLLBACK_INDEX_LOCATION := 6

# vbmeta_system encadenado: system, system_ext y product reconstruidos con
# hashtrees nuevos; el descriptor lo incluye el build desde cada imagen.
BOARD_AVB_VBMETA_SYSTEM := system system_ext product
BOARD_AVB_VBMETA_SYSTEM_KEY_PATH := $(NX733J_AVB_KEYS_DIR)/vbmeta_system.pem
BOARD_AVB_VBMETA_SYSTEM_ALGORITHM := SHA256_RSA4096
BOARD_AVB_VBMETA_SYSTEM_ROLLBACK_INDEX := 1
BOARD_AVB_VBMETA_SYSTEM_ROLLBACK_INDEX_LOCATION := 2

BOARD_AVB_SYSTEM_ADD_HASHTREE_FOOTER_ARGS += --hash_algorithm sha256
BOARD_AVB_SYSTEM_EXT_ADD_HASHTREE_FOOTER_ARGS += --hash_algorithm sha256
BOARD_AVB_PRODUCT_ADD_HASHTREE_FOOTER_ARGS += --hash_algorithm sha256
BOARD_AVB_SYSTEM_ROLLBACK_INDEX := 1
BOARD_AVB_SYSTEM_EXT_ROLLBACK_INDEX := 1
BOARD_AVB_PRODUCT_ROLLBACK_INDEX := 1

# --- Perfil preservado (opcional): vendor/odm/DLKM como imágenes prebuilt ---
# El fragmento privado define BOARD_PREBUILT_*IMAGE y no se incluye solo.
ifneq ($(strip $(NX733J_PRESERVED_MK)),)
-include $(NX733J_PRESERVED_MK)
endif

# Con imágenes preservadas, el vbmeta raíz incorpora sus descriptores stock
# (los bytes son los auditados; no se les añade otro footer).
ifdef BOARD_PREBUILT_VENDORIMAGE
BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS += --include_descriptors_from_image $(BOARD_PREBUILT_VENDORIMAGE)
endif
ifdef BOARD_PREBUILT_ODMIMAGE
BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS += --include_descriptors_from_image $(BOARD_PREBUILT_ODMIMAGE)
endif
ifdef BOARD_PREBUILT_VENDOR_DLKMIMAGE
BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS += --include_descriptors_from_image $(BOARD_PREBUILT_VENDOR_DLKMIMAGE)
endif
ifdef BOARD_PREBUILT_SYSTEM_DLKMIMAGE
BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS += --include_descriptors_from_image $(BOARD_PREBUILT_SYSTEM_DLKMIMAGE)
endif
