$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit_only.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)
$(call inherit-product, vendor/lineage/config/common_full_phone.mk)
$(call inherit-product, device/nubia/nx733j/nx733j.mk)

PRODUCT_NAME := lineage_nx733j
# Identidad en el producto de nivel superior: en Android 16 las variables de
# producto se importan "primer valor gana" y los productos base de AOSP fijan
# PRODUCT_DEVICE=generic; declararlas aquí es el patrón AOSP/Lineage. Verificado
# contra lineage-23.2: TARGET_DEVICE/TARGET_ARCH resuelven nx733j/arm64.
PRODUCT_DEVICE := nx733j
PRODUCT_BRAND := nubia
PRODUCT_MANUFACTURER := nubia
PRODUCT_MODEL := NX733J
PRODUCT_BUILD_GENERIC_OTA_PACKAGE := true
