# Decisiones sobre init.vendor.rc OEM

Fecha: 2026-09-25. Referencia stock NX733J: vendor/etc/init/hw/init.vendor.rc.
No se ejecutó ninguna de sus acciones ni se importó el archivo en el producto.

## Resultado estático

[Inventario](../stock/oem-init-actions.json): 87 bloques de acciones, 397 comandos.
Un nombre no existe en el mapa de builtins del init ROM revisado:
`concat_props_zte`, línea 288, durante post-fs. Se compararon nombres; argumentos,
permisos SELinux y efectos runtime no quedan validados por esa coincidencia.

Por ello, añadir un import del archivo completo no resuelve su dependencia del
init OEM. La presencia de un comando desconocido tampoco significa que todas
las demás acciones se descarten: no se ha ejecutado el parser ROM sobre este rc.

## Clasificación para el primer arranque

| Sección | Contenido observado | Decisión inicial / evidencia pendiente |
| --- | --- | --- |
| early-init:6 | Crea /dev/input | Candidato aislado; necesidad respecto a ueventd por comprobar |
| init:9 | Logs ZTE, permisos de USB/OTG, grupo blkio y peso BFQ | No trasladar como bloque; seleccionar permisos cuando se identifique su consumidor |
| brd-post-fs:27 y late-init:48 | Registros de batería en persist, servicio brd_normal y controles zram | Mantener fuera del port inicial hasta justificar consumidores; no demuestra que sea prescindible para todo uso |
| charger:57 | Montaje directo de persist, registro de batería y propiedad de carga | No usar como ruta normal de montaje; revisar separadamente el arranque charger |
| post-fs:263 | Keybox/omadm, consumer IR, etiquetas de versión y concat_props_zte | Separar generación OEM de propiedades; no importar a ciegas |
| boot:109 | Permisos para múltiples controles OEM | Necesidad por nodo/consumidor aún sin probar |
| post-fs-data:484,674 | Copias/configuración multimedia y permisos de otros subsistemas | Diferido a sus etapas; no se investigó su funcionamiento |
| Triggers de propiedades | Diagnóstico, ajustes, térmica y funciones OEM | No habilitar ni sustituir sin evidencia específica |

El archivo contiene escrituras persistentes y montajes, además de permisos.
El hecho de estar presente en stock no convierte todas sus acciones en requisitos
mínimos del nuevo framework. Se conserva como referencia privada intacta.

## Dependencia USB acotada

init.qcom.usb.rc stock:178–179 usa ro.vendor.product.ztename para el texto product
de los gadgets g1/g2. El comentario OEM atribuye su generación a concat_props_zte,
pero [la evidencia actual](../stock/oem-init-usb-property.json) muestra que:

- vendor/build.prop:795 ya contiene `ro.vendor.product.ztename=nubia Z70 Ultra`.
- La propiedad consultada en el teléfono tiene exactamente ese valor.
- Init ROM carga vendor/build.prop en PropertyLoadBootDefaults
  (property_service.cpp:1223) y publica los valores (:1237–1241).
- PropertyInit llama esa carga (:1439); init.cpp llama PropertyInit (:988)
  antes de cargar scripts (:1046) y encolar early-init (:1067).

[INFERRED] En el perfil de vendor B preservado, esta propiedad puede proceder de
su build.prop sin reimplementar concat_props_zte ni duplicarla en un rc. Requiere
que se cargue esa imagen, que el establecimiento de la propiedad tenga éxito y
que no haya una definición posterior que la cambie. Esto no es prueba de ADB ROM
ni justifica reemplazar los demás efectos de la función OEM desconocida.

## Decisión y próximo paso

No añadir el import global de init.vendor.rc. Mantener la propiedad en su fuente
vendor preservada; no añadir un setprop duplicado ni portar la función OEM completa.

Siguiente revisión: grafo acotado de init.qcom.usb.rc/init.vendor.usb.rc frente a
init.usb.configfs.rc ROM, orden de configuración/UDC y consumidor adbd. El enlace
hacia esos rc ya existe desde init.qcom.rc; no depende del import separado que
originó la auditoría. No activar ni cambiar el modo USB del teléfono durante ella.

El bloqueo general de build continúa por AVB, ramdisk, VINTF/SELinux y dependencias.
No se cambia hardware, firmware, permisos ni política de carga con este documento.

Reproducción:

```text
python tools/audit_oem_init_actions.py <init.vendor.rc> <init/builtins.cpp-ROM> <informe-nuevo.json>
```
