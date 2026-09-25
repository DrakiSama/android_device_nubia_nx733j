# Separación de inventarios por perfil

[Resultado reproducible](../stock/profile-blob-scope.json). Estado PARTIAL:
clasificación por destino, no selección de dependencias ni aprobación de extracción.

| Inventario | Entradas | Alcance en stock-b-build-only |
| --- | ---: | --- |
| proprietary-files.candidates.txt | 3718: vendor 3705, odm 13 | Ya dentro de imágenes preservadas; no instalar individualmente |
| system-ext-product-inventory.txt | 2621: system_ext 2145, product 476 | Particiones reconstruidas; decidir fuente/blob/omisión caso por caso |

CONFIRMED: el inventario histórico no aporta ninguna entrada system/system_ext/product.
Promover su borrador a proprietary-files.txt no resuelve las dependencias externas
del vendor conservado. La cantidad de entradas tampoco mide cuántos blobs necesita
la ROM. No se añade el inventario de aplicaciones stock al producto.

## Frontera del generador

extract-files.py sólo admite el manifiesto genérico proprietary-files.txt, que
sigue ausente. device.mk hereda nx733j-vendor.mk y BoardConfig.mk incluye
BoardConfigVendor.mk, pero no seleccionan perfiles diferentes. Mantener esos
puntos bloqueados hasta diseñar el generador para particiones reconstruidas.
No combinar un vendor generado completo con BOARD_PREBUILT_VENDORIMAGE esperando
que el build decida por sí solo qué archivos y políticas deberían ganar.

La distinción histórica «generado desde fuente» sigue vigente al reconstruir una
partición. No exige retirar build.prop, VINTF o política vendor de una imagen que
se conserva íntegra. Tampoco autoriza usar esa política como política framework.

## Reproducir la clasificación

```text
python tools/audit_profile_blob_scope.py config/bringup-stock-b.json stock/profile-blob-scope-nuevo.json stock/proprietary-files.candidates.txt stock/system-ext-product-inventory.txt
```

Sólo lee inventarios y contrato; no extrae blobs. Rechaza destinos existentes,
duplicados y sintaxis de flags/remapeos de extract-utils: acepta rutas relativas
simples y no intenta adivinar sus destinos. Una entrada en una partición fuera del
perfil queda UNKNOWN. El informe nunca declara extracción aprobada.

## Siguiente selección mínima

Cruzar las referencias externas de init y las dependencias ELF ya inventariadas
con proveedores de la ROM, empezando por boot/ADB. Cada archivo seleccionado debe
indicar consumidor, partición destino, necesidad y evidencia; una coincidencia
DT_NEEDED no prueba namespace ni ABI. Las referencias de servicios OEM no activos
no son por sí mismas requisitos de primer arranque. Mantener cámara/audio/NFC y
aplicaciones fuera de esta selección inicial.
