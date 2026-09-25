# Capas de producto

`nx733j.mk` hereda `device.mk` y declara la identidad del dispositivo. No hereda
configuración de LineageOS ni fija PRODUCT_NAME: cada ROM aporta su wrapper.

`lineage_nx733j.mk` conserva las bases AOSP, common_full_phone de Lineage y el
nombre lineage_nx733j. La secuencia de herencia relevante se conserva: bases,
configuración de la ROM y capa del dispositivo. AndroidProducts.mk mantiene
únicamente la entrada existente; no se anuncia un producto AOSP compilable nuevo.

Para otro derivado, el wrapper debe seleccionar sus bases y nombre de producto
e incorporar nx733j.mk. La resolución de kernel/AVB/vendor/VINTF/SELinux sigue
siendo requisito; esta separación no prueba compatibilidad con otra ROM.

No se cambió identidad, arquitectura, tamaño de particiones o política AVB.
No se ejecutó un build ni una prueba de evaluación de makefiles.
