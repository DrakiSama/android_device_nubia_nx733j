# Contrato ADB para el producto mínimo

Estado: PARTIAL; revisión de fuentes, sin build, arranque ROM ni cambio en stock.
[Fuentes identificadas](../stock/adb-product-contract.json).

## Provisión del producto

CONFIRMED en fuentes: lineage_nx733j.mk hereda full_base_telephony.mk. La cadena
continúa por aosp_base.mk, full_base.mk, generic_no_telephony.mk,
handheld_system.mk, media_system.mk y base_system.mk. Este último incluye
adbd_system_api (:21) y com.android.adbd (:52). La existencia de esa cadena no
sustituye la evaluación final de Make/Soong ni descarta overrides posteriores.

packages/modules/adb/apex/Android.bp:15 incluye el binario adbd y :27 su rc.
Android.bp:604–609 incorpora daemon/usb.cpp y usb_ffs.cpp para Android mediante
libadbd_core. El binario usa daemon/main.cpp (:801–803).
Decisión: no duplicar PRODUCT_PACKAGES, copiar adbd stock ni añadir un servicio
propio en el device tree. Otro wrapper AOSP deberá heredar una base equivalente.

## Arranque y FunctionFS

CONFIRMED en fuentes:

- system/core/rootdir/init.usb.rc:15–21 define adbd disabled/updatable.
  El rc del APEX declara override para ese servicio.
- init.rc:571 encola post-fs-data antes de zygote-start (:578). Dentro de
  post-fs-data espera apexd.status=activated y ejecuta perform_apex_config
  (:1049–1051). Esto describe el orden programado, no garantiza que se complete.
- El vendor preservado monta FunctionFS en zygote-start; véase la auditoría USB.
- daemon/main.cpp:256–261 llama usb_init solamente si access(ep0,F_OK) tiene éxito.
  No asumir que el bucle interno de reintentos de usb.cpp resuelve un ep0 ausente
  antes de seleccionar el backend: ese bucle todavía no se habría iniciado.
- daemon/main.cpp:141–144 cambia UID/GID a shell si reduce privilegios. El propietario
  shell y modo 0660 de los endpoints stock son coherentes con acceso DAC en esa
  rama. Los grupos suplementarios están enumerados en :115–119; no inventar grupos.
- private/property_contexts:905 etiqueta sys.usb.ffs.ready como ffs_control_prop
  de tipo bool. private/adbd.te:84 permite set_prop(adbd, ffs_control_prop).

INFERRED: la base ya contiene las piezas para el contrato ADB/FunctionFS observado.
UNKNOWN: composición evaluada del producto, disponibilidad efectiva del APEX,
orden completo frente a triggers OEM, política combinada vendor/framework y éxito
al arrancar. No añadir permisivo, autorización ADB automática o adbd root como
solución a estos pendientes.

## Condición de integración

Antes de marcar ADB listo: asegurar que el montaje y ep0 precedan al inicio
real de adbd, que el APEX suministre el servicio esperado y que la política
combinada conserve los permisos indicados. No forzar ahora un start/restart ni
cambiar el modo USB del teléfono para simular una ROM que aún no existe.

Siguiente trabajo de base: integrar de forma explícita el perfil de imágenes
preservadas con el producto y el proveedor kernel, manteniendo el build bloqueado
hasta cerrar AVB/ramdisk/VINTF/SELinux. La herencia actual del vendor generado y
el perfil de vendor completo preservado todavía son alternativas sin seleccionar.
