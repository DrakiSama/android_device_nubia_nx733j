# usbconfig: análisis estático y frontera de decisión

Fecha: 2026-09-26. Alcance: análisis de solo lectura de la copia privada del
binario OEM `/system/bin/usbconfig`. No se ejecutó, no se publicó y no se
modificó el teléfono. Complementa la [frontera USB](USB-INIT-BOUNDARY.md) y la
[identidad ELF](../stock/usbconfig-elf.json) (SHA-256
a260eb2db7d4f494b5177f24d53a30f973ab3dcc38742db24154e1c7a2f6d27a, 377840 bytes).

## Método

- `file`: ELF 64-bit aarch64, **statically linked, stripped**, BuildID
  4c0499fd20fbdbacf458724ec3eb7c52, `.note.android.ident` NT_VERSION 36.
  Sin PT_DYNAMIC ni PT_INTERP: **no existen dependencias dinámicas**; el
  analizador previo no omitió una tabla, no hay tabla que leer. El cierre de
  dependencias es kernel (syscalls) más el propio código.
- `strings` filtrado: el binario enlaza libc/scudo/libunwind/libc++ estáticos;
  casi todos los strings son de esas bibliotecas. Se aislaron los identificadores
  propios del OEM.
- Desensamblado con `llvm-objdump` de los prebuilts LineageOS (el `objdump` de
  WSL es solo x86) y búsqueda de referencias `adrp`/`add` a cada string propio.
  Todo el código propio identificado cae en un bloque contiguo
  (~0x214100–0x214260), coherente con una única función.

## Evidencia estática (CONFIRMED)

Strings propios y sus referencias:

| String | Dirección | Xrefs |
| --- | --- | --- |
| `/sys/devices/virtual/android_usb/android0/manu_tag` | 0x2025d4 | 3 (carga del path para apertura/lectura) |
| `usbconfig read usbmanutag failed!` | 0x200d97 | 1 |
| `start usb property config` | 0x202d66 | 1 |
| `sys.usb.config` | 0x201fa7 | 1 |
| `diag,adb,facmode` | 0x203f6c | 1 |
| `property_set USB_PROPERTY fail` | 0x20217e | 1 |
| `sys.usb.factory` | 0x2034a0 | 1 |
| `property_set USB_FAC_TAG_KEY fail` | 0x2010a7 | 1 |
| `/dev/block/by-name/ztecfg` | 0x201066 | referencia en otro bloque (no aislada) |
| `/dev/block/bootdevice/by-name/ztecfg` | 0x204aca | no referenciado por adrp/add directo |

El bloque único carga primero el path de `manu_tag` (0x214100), registra el
fallo de lectura si no puede (0x214140), y en la rama de éxito registra
`start usb property config` (0x2141f4), carga `sys.usb.config` +
`diag,adb,facmode` (0x214218/0x214200) y `sys.usb.factory` (0x214238) junto a
sus mensajes de fallo de `property_set` (0x21422c/0x214250). INFERRED por
adyacencia y orden de carga: el programa lee el manufacturing tag y, si lo
obtiene, publica `sys.usb.config=diag,adb,facmode` y la clave del tag en
`sys.usb.factory`. No configura enlaces configfs, UDC ni adbd: solo propiedades.

## Contraparte en el vendor preservado (CONFIRMED)

- `vendor/etc/init/hw/init.vendor.usb.rc:45` declara `service usbconfig
  /system/bin/usbconfig` (class main, root, oneshot, sin `disabled`): se ejecuta
  una vez por arranque. Es su única declaración; no hay `start usbconfig`
  explícito.
- Mismo archivo, :498/:501, :519/:522 y :593/:596 reaccionan a
  `sys.usb.config=diag,adb,facmode`, `diag,diag_mdm,adb,facmode` y
  `rndis,diag,diag_mdm,adb,facmode` con el gadget configfs (Vendor 0x19d2).
- Mismo archivo, :905–906: `on property:sys.usb.factory=clear` escribe `0` en
  `/sys/class/android_usb/android0/manu_tag` (operación inversa del binario).
- `vendor/etc/init/hw/init.qcom.factory.rc:118, :121, :129, :133`: en bootmodes de fábrica
  (`ffbm-01/02/99`, trigger `mmi`) hace `setprop sys.usb.factory enable` y
  `setprop sys.usb.config diag,adb,facmode`; además escribe atributos
  `noSerialno`, `rebootFtm` y `forceSwitch` del gadget legacy.

## Estado vivo en el dispositivo (CONFIRMED, solo lectura)

Slot B, root, mismo arranque de las auditorías anteriores:

- `/sys/devices/virtual/android_usb/android0/` expone únicamente
  `f_midi, power, state, subsystem, uevent`. **`manu_tag` no existe** (tampoco
  `forceSwitch`, `noSerialno` ni `rebootFtm`), así que la lectura del binario
  falla y no llega a publicar propiedades. El kernel stock carece también de
  los atributos que las ramas de fábrica intentan escribir.
- `sys.usb.factory` vacío, `init.svc.usbconfig=stopped`, `ro.bootmode` no es
  `ffbm-*`. ADB y la composición USB de consumidor funcionan sin intervención
  del binario.
- SELinux: `vendor/etc/selinux/vendor_file_contexts:1093` etiqueta
  `/sys/devices/virtual/android_usb/android0(/.*)?` como `sysfs_usbscript`;
  `usbscript_exec` y `sysfs_usbscript` se definen en la política vendor. La
  etiqueta `usbscript_exec` del binario stock en `/system/bin/usbconfig` proviene
  de la política plat OEM, no de vendor.

## Interpretación

`usbconfig` es un helper de **modo fábrica/producción**: reaplica en cada
arranque la composición USB de fábrica (`diag,adb,facmode`) cuando el
manufacturing tag está grabado. No interviene en el arranque de consumidor, no
monta FunctionFS, no arranca adbd y no es necesario para ADB. En el kernel
actual el nodo que lee no existe, por lo que su ejecución es inoperante incluso
en stock; las propias ramas de fábrica del vendor escriben atributos que este
kernel no expone.

## Respuestas al handoff

1. ¿Imprescindible para boot/USB/ADB? No hay evidencia: en el arranque de
   consumidor falla su lectura y ADB/USB funcionan; sus únicas salidas son dos
   propiedades de fábrica.
2. ¿Reemplazable por comportamiento estándar? Para consumidor no hay nada que
   reemplazar. La composición de fábrica ya la aplica `init.qcom.factory.rc`
   cuando el bootmode es `ffbm-*`; el binario solo la replica por tag.
3. ¿Eliminable modificando init? La declaración vive en el vendor preservado
   (no editable sin cambiar su imagen). Sin el ejecutable, init registra un
   fallo de exec del servicio una vez por arranque; no afecta USB/ADB.
4. ¿Requiere conservar un componente OEM? No para el perfil de consumidor.
   Solo tendría sentido con un flujo de fábrica soportado.
5. ¿Implementación equivalente en fuentes públicas? El patrón ZTE/Nubia de
   `sys.usb.factory`/composiciones `diag,adb` aparece en árboles públicos
   (p. ej. `android_device_nubia_msm8998-common`, `init.msm.usb.configfs.rc`)
   como reglas init; no existe fuente del binario.
6. ¿Referencias reconstruibles sin el binario? Sí: si alguna vez se exigiera el
   flujo, una acción init puede leer `manu_tag` (cuando exista) y publicar
   `sys.usb.factory`/`sys.usb.config`; no requiere el binario propietario.

## Decisión propuesta (pendiente de aprobación explícita)

Excluir `usbconfig` del system reconstruido y no empaquetar el binario OEM:
no es necesario para el arranque de consumidor, su función es de fábrica, y su
etiqueta SELinux stock no es reproducible desde la política plat de LineageOS
(referiría a un tipo vendor). Se acepta como ruido de baja severidad el fallo
de exec del servicio declarado en el vendor preservado. No se añade dominio
SELinux, binario ni script sustituto. Se revisará solo si aparece un requisito
real de modo fábrica, momento en que se preferirá una acción init documentada
antes que el binario propietario.

## Límites

El análisis es estático: no demuestra el comportamiento en ejecución ni cubre
kernels OEM antiguos (`ffbm`) ni el flujo de calibración real. La ausencia de
los atributos OEM del gadget se verificó en este kernel (6.6.92) y este
arranque; debe revalidarse si cambia el kernel o el firmware. No se cambiaron
propiedades, modos USB ni servicios del teléfono. El binario privado no se
publica.

## Reproducción

```text
# Solo sobre la copia privada; el binario no está en el repositorio.
file <copia>                     # estatico aarch64 stripped
strings -a -n 5 <copia>          # identificadores propios del OEM
llvm-objdump -d --no-show-raw-insn <copia>   # xrefs adrp/add a los strings
```

La comparación de rc se hizo sobre el vendor extraído de la auditoría
2026-09-23; las consultas al teléfono fueron `ls`/`getprop`/`grep` de solo
lectura con root.
