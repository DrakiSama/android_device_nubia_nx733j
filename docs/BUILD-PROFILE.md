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
las imágenes y el adaptador privado ya están preparados; falta integrar el
producto y revisar el uso final de AVB/target_files. El proveedor de módulos sueltos no sustituye esas
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

## Identidad de imágenes completas cerrada

[Informe](../stock/preserved-images-audit.json): las cuatro imágenes existentes
coinciden por SHA-256 con sus extents de super B. Se comprobaron nuevamente los
bytes de metadatos primario/backup usados para leer el mapa. Cada imagen tiene
footer al final y su descriptor hashtree interno coincide con el del vbmeta B.
No se volvieron a copiar imágenes ni se publicó ningún binario. FEC sigue pendiente.

El contrato JSON registra tamaños, hashes completos y hashes de descriptores.
Las rutas absolutas están únicamente en el mapa local privado. Falta conectar
esas rutas a un adaptador y comprobar su uso en target_files/AVB; identidad de
entrada no equivale a integración compilada.

```text
python tools/audit_preserved_images.py <avbtool.py> <super.img> stock/edl-audit-2026-09-23/super-metadata-audit.json <mapa-privado.json> <vbmeta_b.img> <informe-nuevo.json>
```

El mapa privado tiene cuatro claves: vendor, odm, vendor_dlkm y system_dlkm;
sus valores son rutas locales a las imágenes completas.

### Diferencia respecto al inventario para reconstruir vendor

La clasificación histórica de blobs corresponde a reconstruir vendor/odm.
Este perfil conserva sus imágenes completas, incluidos VINTF, propiedades y
política vendor existentes. **No usa la política compilada vendor como sustituto
de la política fuente del framework nuevo.** Debe comprobar compatibilidad de
versiones/mappings SELinux y VINTF, y el tratamiento del precompiled_sepolicy.
No se borran archivos internos de los prebuilts para aparentar compatibilidad.
El inventario antiguo no se promueve automáticamente al producto conservado.

Preparación posterior: [adaptador privado de entradas](PRESERVED-IMAGE-INPUTS.md),
sin activar el perfil ni seleccionar una política de firma.
