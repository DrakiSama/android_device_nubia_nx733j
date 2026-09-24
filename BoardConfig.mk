DEVICE_PATH := device/nubia/nx733j
TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-a
TARGET_CPU_ABI := arm64-v8a
TARGET_CPU_VARIANT := generic
TARGET_CPU_VARIANT_RUNTIME := oryon
TARGET_BOARD_PLATFORM := sun
TARGET_BOOTLOADER_BOARD_NAME := sun
TARGET_NO_BOOTLOADER := true

# Header sizes/format verified from installed images; see stock/boot-audit.json.
BOARD_BOOT_HEADER_VERSION := 4
# mkbootimg does not derive its CLI header version from the board variable.
# init_boot has a separate argument list; see docs/BOOT-BUILD-COMPOSITION.md.
BOARD_MKBOOTIMG_ARGS += --header_version $(BOARD_BOOT_HEADER_VERSION)
BOARD_MKBOOTIMG_INIT_ARGS += --header_version $(BOARD_BOOT_HEADER_VERSION)
BOARD_KERNEL_PAGESIZE := 4096
# Stock vendor_boot stores absolute load addresses. Base zero is the chosen
# mkbootimg representation of those values, not a GPT/flash offset.
BOARD_KERNEL_BASE := 0x00000000
BOARD_MKBOOTIMG_ARGS += --kernel_offset 0x00008000
BOARD_MKBOOTIMG_ARGS += --ramdisk_offset 0x01000000
BOARD_MKBOOTIMG_ARGS += --tags_offset 0x00000100
BOARD_MKBOOTIMG_ARGS += --dtb_offset 0x01f00000
BOARD_RAMDISK_USE_LZ4 := true
BOARD_EXCLUDE_KERNEL_FROM_RECOVERY_IMAGE := true
AB_OTA_UPDATER := true
# Provisional OTA scope. Resolve pvmfw (referenced by stock vbmeta_system)
# and which vendor partitions will be built before enabling a release.
AB_OTA_PARTITIONS := boot init_boot vendor_boot recovery dtbo vbmeta vbmeta_system system system_ext product vendor odm vendor_dlkm system_dlkm

BOARD_BOOTIMAGE_PARTITION_SIZE := 100663296
BOARD_INIT_BOOT_IMAGE_PARTITION_SIZE := 8388608
BOARD_VENDOR_BOOTIMAGE_PARTITION_SIZE := 100663296
BOARD_RECOVERYIMAGE_PARTITION_SIZE := 104857600
BOARD_DTBOIMG_PARTITION_SIZE := 25165824
BOARD_SUPER_PARTITION_SIZE := 17179869184
BOARD_SUPER_PARTITION_GROUPS := qti_dynamic_partitions
BOARD_QTI_DYNAMIC_PARTITIONS_SIZE := 17175674880
BOARD_QTI_DYNAMIC_PARTITIONS_PARTITION_LIST := system system_ext product vendor odm vendor_dlkm system_dlkm

TARGET_COPY_OUT_VENDOR := vendor
TARGET_COPY_OUT_ODM := odm
TARGET_COPY_OUT_PRODUCT := product
TARGET_COPY_OUT_SYSTEM_EXT := system_ext
TARGET_COPY_OUT_VENDOR_DLKM := vendor_dlkm
TARGET_COPY_OUT_SYSTEM_DLKM := system_dlkm
BOARD_VENDORIMAGE_FILE_SYSTEM_TYPE := erofs
BOARD_ODMIMAGE_FILE_SYSTEM_TYPE := erofs
BOARD_VENDOR_DLKMIMAGE_FILE_SYSTEM_TYPE := erofs
BOARD_SYSTEM_DLKMIMAGE_FILE_SYSTEM_TYPE := erofs
TARGET_USERIMAGES_USE_EXT4 := true
TARGET_USERIMAGES_USE_F2FS := true
BOARD_USES_METADATA_PARTITION := true

# Mandatory, intentionally absent until kernel, AVB chain, SEPolicy and HAL
# choices have been verified. Prevent producing an accidentally flashable ROM.
include $(DEVICE_PATH)/BoardConfigBringup.mk
include vendor/nubia/nx733j/BoardConfigVendor.mk
