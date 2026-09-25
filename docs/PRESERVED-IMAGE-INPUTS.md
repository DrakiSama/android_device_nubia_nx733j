# Entradas privadas de imágenes preservadas

Estado: PREPARED_NOT_ACTIVATED. [Resultado sin rutas privadas](../stock/preserved-input-preparation.json).

## Preparación realizada

La herramienta tools/prepare_preserved_image_inputs.py comprobó las cuatro
imágenes del contrato stock B: vendor, odm, vendor_dlkm y system_dlkm.
Se leyeron 1982107648 bytes; tamaños y SHA-256 coinciden con el perfil registrado.
Generó enlaces Linux y BoardConfigPreservedImages.mk en un directorio privado nuevo.
No duplicó ni modificó imágenes originales; no añadió includes al device tree.

El fragmento contiene las cuatro variables BOARD_PREBUILT_*IMAGE correspondientes.
Su ruta no tiene espacios ni metacaracteres Make; los enlaces pueden apuntar a
los archivos originales con espacios en su ubicación. El manifiesto privado
conserva las rutas originales; no se publica ese archivo ni las imágenes.

## Reproducir en Linux

```text
python3 tools/prepare_preserved_image_inputs.py config/bringup-stock-b.json /ruta/mapa-privado.json /ruta/nueva-sin-espacios
```

El mapa contiene exactamente vendor, odm, vendor_dlkm y system_dlkm, cada uno
con su ruta Linux a la imagen completa. La herramienta exige el perfil NX733J B
inactivo, verifica todas las entradas antes de crear el destino y rechaza destinos
existentes. Si hay un fallo de escritura, conserva las salidas parciales para
inspección; no elimina archivos ni sobrescribe un intento anterior.

Los enlaces NO inmovilizan el contenido. Volver a comprobar identidad antes de
cada build y proteger las fuentes de cambios concurrentes. Esta preparación no
valida firmas AVB, FEC, compatibilidad framework/vendor ni restauración.

## Interfaz del build inspeccionada

CONFIRMED en el checkout build/make registrado en build-interface-reference.json:
core/Makefile copia los prebuilts en las ramas :4089–4091 (vendor), :4335–4337
(odm), :4404–4406 (vendor_dlkm), :4544–4546 (system_dlkm). Las ramas target_files
incluyen dependencias (:6525, :6560, :6569, :6587) y copias a IMAGES (:6944,
:6972, :6976, :6984). Esto demuestra interfaces de fuente, no su ejecución.

## Activación pendiente

No incluir el fragmento todavía: la herencia actual de nx733j-vendor.mk y
BoardConfigVendor.mk pertenece al perfil de blobs generados. Hay que separar
las dependencias para system/system_ext/product, evitar reconstruir las cuatro
particiones preservadas y definir el tratamiento de VINTF/SELinux y AVB nuevo.
BoardConfigBringup.mk sigue ausente deliberadamente; no se ha habilitado build,
OTA ni flasheo. La selección de proveedor kernel sigue siendo independiente.
