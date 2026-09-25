# Primer perfil: stock B, sólo compilación

Fecha: 2026-09-25. [Contrato de decisiones](../config/bringup-stock-b.json).
Estado: DESIGN_NOT_ACTIVATED. Es una decisión de ingeniería para reducir variables,
no una propiedad stock confirmada ni una autorización de instalación.

| Particiones | Productor inicial | Tratamiento AVB |
| --- | --- | --- |
| system, system_ext, product | Fuentes ROM + dependencias OEM mínimas identificadas | Nuevos hashtrees |
| vendor, odm, vendor_dlkm, system_dlkm | Imágenes completas stock B preservadas | Descriptores correspondientes a esos bytes |
| boot | Kernel stock, empaquetado ROM | Metadata nueva; cadena por definir |
| init_boot | Init/ramdisk construidos desde fuentes | Metadata nueva |
| vendor_boot | DTB y módulos stock; ramdisk de plataforma portado | Metadata nueva |
| recovery | Recovery ROM separado, sin kernel dentro | Metadata nueva; cadena por definir |
| dtbo | Payload stock dentro de la entrada auditada de 18 MiB | Descriptor recalculado durante empaquetado |
| pvmfw | Firmware B preservado y comprobado | Sólo su descriptor, asociado a ese firmware |
| vbmeta, vbmeta_system | Construcción nueva | Claves explícitas del producto |

Conservar vendor/odm y ambos DLKM evita reconstruir simultáneamente sus archivos,
etiquetas y módulos. **No elimina** sus dependencias OEM en system_ext/product,
ni demuestra compatibilidad VINTF con el framework nuevo. La lista candidata de
blobs deberá separar los prebuilts conservados de los archivos requeridos en las
particiones reconstruidas; el generador vendor actual aún no implementa ese perfil.

La interfaz local soporta BOARD_PREBUILT_VENDORIMAGE, BOARD_PREBUILT_ODMIMAGE,
BOARD_PREBUILT_VENDOR_DLKMIMAGE y BOARD_PREBUILT_SYSTEM_DLKMIMAGE. No se asignaron:
falta preparar y registrar todas las imágenes privadas completas y revisar los
consumidores AVB/target_files. El proveedor de módulos sueltos no sustituye esas
imágenes. Los tipos EROFS existentes también sirven para un perfil futuro que
reconstruya esas particiones; no fuerzan por sí solos esta decisión.

## Frontera AVB y OTA

- AVB permanece requerido: no se elude desactivando verificación.
- Claves e índices de rollback quedan sin valor hasta definir la política del
  producto. No se usan claves OEM ni se seleccionan automáticamente test keys.
- No se importa vbmeta_system stock completo: sus descriptores de system,
  system_ext y product quedarían obsoletos después de reconstruirlos.
- El perfil no es OTA. No cambia AB_OTA_PARTITIONS ni habilita un paquete instalable.
  La lista existente sigue siendo provisional y la compilación sigue bloqueada.
- B identifica la **procedencia** del firmware. No autoriza un slot destino.
  Un futuro instalador deberá comprobar la identidad de cada partición preservada
  en el slot elegido. pvmfw A y B difieren; no se resuelve copiando entre slots.

## Orden de implementación

1. Preparar manifiesto de imágenes completas privadas vendor/odm/DLKM y sus
   descriptores; comprobar contra la evidencia del respaldo.
2. Separar extracción de dependencias necesarias en particiones reconstruidas.
3. Resolver fstab/cmdline/bootconfig y etiquetas de primera etapa.
4. Elegir firma y cadena nuevas con control de firmware conservado por slot.
5. Conectar el perfil al build; resolver VINTF/SELinux antes de quitar el bloqueo.

No se generaron imágenes ROM ni se ejecutaron pruebas de compilación. Este archivo
fija el alcance inicial y permite sustituir el proveedor kernel o adoptar otro
perfil más adelante sin convertir las decisiones stock en reglas universales.
