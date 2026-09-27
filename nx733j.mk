# Device product layer shared by ROM wrappers. No ROM-specific inheritance.
# La identidad (PRODUCT_DEVICE/BRAND/MANUFACTURER/MODEL) se declara en el
# makefile de producto de nivel superior de cada ROM, no aquí: en Android 16 la
# captura de variables usa "primer valor gana" y los productos base de AOSP
# fijan PRODUCT_DEVICE=generic. Patrón AOSP/Lineage; ver docs/PRODUCT-LAYERS.md.
$(call inherit-product, device/nubia/nx733j/device.mk)
