DEVICE_PATH := device/nubia/nx733j
PRODUCT_SHIPPING_API_LEVEL := 35
PRODUCT_USE_DYNAMIC_PARTITIONS := true
$(call inherit-product, $(SRC_TARGET_DIR)/product/virtual_ab_ota/compression_with_xor.mk)
PRODUCT_SOONG_NAMESPACES += $(DEVICE_PATH)

# Generate this using extract-files.py after reviewing proprietary-files.txt.
$(call inherit-product, vendor/nubia/nx733j/nx733j-vendor.mk)

# HALs, overlays, init and vendor properties must be ported from the audited
# stock configuration. Do not inherit the TWRP product or another OEM's tree.
