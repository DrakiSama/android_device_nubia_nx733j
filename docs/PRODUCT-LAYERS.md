# Capas de producto

`nx733j.mk` hereda `device.mk`: es la capa de dispositivo compartida, sin
configuración de LineageOS ni PRODUCT_NAME.

**La identidad del dispositivo se declara en el makefile de producto de nivel
superior de cada ROM** (`lineage_nx733j.mk` y cualquier wrapper futuro). Motivo
verificado contra lineage-23.2: en Android 16 las variables de producto se
importan con «primer valor gana» y los productos base de AOSP fijan
`PRODUCT_DEVICE := generic`; declarar la identidad solo en una capa heredada
deja el producto resuelto como `generic` (arm/generic) y sin BoardConfig
aplicado. Con la identidad en el nivel superior, `TARGET_DEVICE=nx733j`,
`TARGET_ARCH=arm64` y el resto de la configuración se aplican.

`lineage_nx733j.mk` conserva las bases AOSP, common_full_phone de Lineage, el
nombre lineage_nx733j y la identidad. AndroidProducts.mk mantiene únicamente la
entrada existente; no se anuncia un producto AOSP compilable nuevo.

Para otro derivado, el wrapper debe seleccionar sus bases y nombre de producto
e incorporar nx733j.mk. La resolución de kernel/AVB/vendor/VINTF/SELinux sigue
siendo requisito; esta separación no prueba compatibilidad con otra ROM.

No se cambió identidad, arquitectura, tamaño de particiones o política AVB.
No se ejecutó un build ni una prueba de evaluación de makefiles.
