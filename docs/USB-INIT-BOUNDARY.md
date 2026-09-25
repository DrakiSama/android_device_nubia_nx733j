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

## Captura inicial NX733J (contexto shell)

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

## Corrección: contexto de consulta y regla RNDIS

[Evidencia adicional](../stock/usb-init-root-context.json), consultada en el mismo
boot y comparando shell/root secuencialmente:

| Propiedad | Shell | Root |
| --- | --- | --- |
| sys.usb.ffs.ready | vacío | 1 |
| vendor.usb.use_ffs_mtp | vacío | 1 |
| vendor.usb.controller | vacío | a600000.dwc3 |
| vendor.usb.rndis.func.name | vacío | gsi |
| init.svc.vendor.usb-hal | vacío | running |
| persist.vendor.usb.config | vacío | vacío |

CONFIRMED: el contexto de consulta cambia la visibilidad observada. La captura
anterior conserva las salidas reales de shell, pero sus vacíos NO describen la
vista de init/root. No se ha establecido el mecanismo exacto de esa diferencia.
En capturas futuras, consultar estas propiedades con root y registrar el contexto.

CONFIRMED: init.vendor.usb.rc:238–256 tiene una rama exacta para rndis,none,adb.
Arranca adbd; con ffs.ready=1 configura f1 mediante vendor.usb.rndis.func.name,
f2 mediante ffs.adb, escribe UDC y publica deliberadamente sys.usb.state=rndis,adb.
Por tanto, la diferencia config/state no es por sí misma una incompatibilidad:
está expresamente prevista en stock. Los valores root y enlaces capturados son
compatibles con esta rama (INFERRED), sin demostrar su ejecución histórica.
La fuente ROM init.usb.configfs.rc:131–139 utiliza rndis,adb, una condición distinta.

CONFIRMED: vendor/etc/init/android.hardware.usb-service.qti.rc declara
vendor.usb-hal, binario /vendor/bin/hw/android.hardware.usb-service.qti, class hal,
usuario system y grupos system/mtp/usb. Su manifest declara AIDL
android.hardware.usb.IUsb/default. Se observa servicio registrado y estado running
con root. Ambos archivos coinciden por SHA-256 con el teléfono.
Esto identifica el HAL de puerto; no demuestra un HAL gadget ni que ese proceso
sea el responsable de escribir la composición configfs.

## Bloqueo restante y siguiente paso

La composición RNDIS observada tiene ahora una explicación estática NX733J.
Se corrige la interpretación anterior, sin modificar ninguna propiedad del teléfono.
Permanece la superposición OEM/ROM para adb y mtp,adb descrita arriba: no activar
la integración hasta decidir quién configura enlaces, UDC y sys.usb.state.

UNKNOWN: historial real de ejecución, posibles escritores adicionales del gadget,
integración de adbd ROM y permisos SELinux. Siguiente objetivo: comparar los rc
USB del sistema stock con ROM y rastrear la creación de ffs.adb/montaje FunctionFS,
para diseñar un único responsable de composición en el perfil de bring-up.
No hacen falta nuevos dumps de particiones ni cambiar el modo USB.
