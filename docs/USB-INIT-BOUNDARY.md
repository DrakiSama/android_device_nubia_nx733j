# Frontera USB entre stock e init ROM

## Alcance

Auditoría de lectura, sin cambiar composición USB, reiniciar servicios ni flashear.
[Evidencia acotada](../stock/usb-init-boundary.json): propiedades, enlaces configfs,
SHA-256 de fuentes y extractos con líneas. Las dos fuentes vendor coinciden byte
por byte con los archivos vivos. La fuente ROM es el checkout local de system/core,
no un binario arrancado. No se ha compilado ni probado una ROM.

## Hallazgos

| Estado | Archivo / sección | Problema o evidencia | Decisión |
| --- | --- | --- | --- |
| CONFIRMED | init.qcom.rc:63–64 | Importa ambos rc USB independientemente de init.vendor.rc | Mantener separada la decisión sobre el import OEM global |
| CONFIRMED | init.qcom.usb.rc:177–190 | Ejecuta script USB, configura nombre, añade funciones MTP/PTP y toma persist.vendor.usb.config en boot | No asumir que este bloque explica la configuración observada |
| CONFIRMED | init.vendor.usb.rc:354–385 y ROM init.usb.configfs.rc:31–40 | Ambos arrancan adbd para mtp,adb; ambos pueden escribir f1/f2 y UDC cuando ffs.ready=1; OEM distingue use_ffs_mtp=0/1, ROM usa mtp.gs0 | Hay superposición estática; no activar ambos como integración validada |
| CONFIRMED | init.vendor.usb.rc:445–461 y ROM init.usb.configfs.rc:14–23 | Para adb y ffs.ready=1 ambos escriben UDC; OEM anuncia charging,adb y ROM anuncia adb | Valores distintos para el mismo evento; falta establecer orden y propietario efectivo |
| INFERRED | Composición ROM con vendor preservado | Reejecución de enlaces o escrituras sobre un gadget ya conectado podría fallar o dejar estado distinto | No declarar fallo real a partir de la lectura; requiere resolver arquitectura antes de activar |

## Captura NX733J

CONFIRMED en esta captura, slot B, firmware 20260210.135030:

- ro.boot.usbcontroller, sys.usb.controller y g1/UDC: a600000.dwc3.
- sys.usb.config: rndis,none,adb; sys.usb.state: rndis,adb.
- sys.usb.configfs=1; init.svc.adbd=running.
- f1 enlaza gsi.rndis y f2 enlaza ffs.adb.
- getprop devuelve vacío para vendor.usb.controller, sys.usb.ffs.ready,
  vendor.usb.use_ffs_mtp y persist.vendor.usb.config. No distingue ausente de vacío.

La identidad de boot permaneció igual antes/después. Las consultas son secuenciales:
no constituyen una instantánea atómica ni prueban qué actor creó los enlaces.
El dispositivo está rooteado; no se atribuye automáticamente todo estado vivo al
firmware original. ADB funciona en este teléfono, pero eso no valida ADB en la ROM.

## Bloqueo y siguiente paso

La composición viva no puede explicarse solamente por las ramas adb/mtp,adb leídas.
Se detiene la activación de esta integración y se reporta la discrepancia; no se
corrigen propiedades, reglas ni enlaces del teléfono para hacerlos coincidir.

UNKNOWN: actor efectivo que configura el gadget (HAL, reglas adicionales u otro
componente), orden de escrituras, integración de adbd ROM y permisos SELinux.
Siguiente objetivo: identificar en lectura el servicio USB registrado/en ejecución,
su declaración init/VINTF y las reglas exactas de rndis,none,adb/rndis,adb. Comparar
la selección de reglas del sistema stock y ROM antes de diseñar un único responsable
de composición. No hacen falta nuevos dumps de particiones ni cambiar el modo USB.
