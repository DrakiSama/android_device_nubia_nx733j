# Auditoría ELF y particiones adicionales — 2026-09-23

Estado: capturas extraídas y dependencias por nombre inventariadas. El árbol sigue
sin ser compilable; este informe no valida ABI, VINTF ni soporte de hardware.

## Captura y procedencia

Se reutilizaron vendor/odm del 17 de septiembre, verificando sus hashes antes de
extraer EROFS. Se capturaron system_ext (884314112 bytes) y product (1984057344
bytes) del slot B con root, verificando tamaño y SHA-256 local y en el teléfono
antes/después de cada transferencia. Fingerprints y slot permanecieron estables
y coinciden con la versión del dump anterior. Las imágenes proceden de Android
instalado con root, no de un paquete OEM autenticado. No se validaron firmas AVB.

Los hashes y propiedades están en `stock/elf-audit.json`. Imágenes y binarios
quedan fuera de Git en `diagnostics/rom-audit-2026-09-23/` del workspace ROM.
Las cuatro particiones se extrajeron con `fsck.erofs --no-preserve --extract=...`
en Linux, conservando los symlinks como tales y sin seguirlos al analizar ELF.

## Resultados comprobados

| Partición | ELF64 analizados |
| --- | ---: |
| vendor | 1781 |
| odm | 0 |
| system_ext | 554 |
| product | 58 |
| Total | 2393 |

- Cero errores de lectura/parseo. DT_NEEDED y DT_SONAME de los 2393 archivos
  coinciden con GNU readelf; ocho pruebas de regresión pasaron en Linux.
- Se registran 71 ELF32 no analizados por el parser: tres EM_ARM, veinte
  EM_XTENSA y 48 EM_HEXAGON. Incluyen firmware y bibliotecas DRM de 32 bits.
  No omitirlos silenciosamente ni habilitar soporte ARM32 sin estudiar su uso.
- Hay 81 nombres DT_NEEDED sin proveedor en estas cuatro imágenes; todos tienen
  coincidencias de nombre en el inventario vivo `/system/lib64` o `/apex`.
  Las coincidencias son rutas, no pruebas de arquitectura/símbolos/visibilidad.
  Incluyen bibliotecas del sistema como libc; no son 81 fallos del teléfono.
- 103 nombres usados desde vendor/odm también tienen candidatos en system_ext
  o product. TODOS tienen además candidatos en vendor/odm: no hay evidencia
  de que se deban copiar las variantes de system_ext por esa coincidencia.
- `stock/system-ext-product-inventory.txt` registra 2621 archivos regulares
  de esas dos particiones, no una lista aprobada para extract-utils.

## Hallazgo específico: servicio OEM en system

`bootservice`, `ssdaemon` y `vendorcfg` de system_ext dependen de
`/system/lib64/libvendorcfg.oem.so`, fuera de los cuatro inventarios principales.
Se obtuvo autorización específica para copiar ese archivo (51712 bytes) solo
localmente. Se verificó SHA-256 y se analizaron sus siete DT_NEEDED; el binario
NO forma parte del repositorio. Sus metadatos figuran en `stock/elf-audit.json`.

Antes de portarlo, decidir si esos tres servicios OEM son necesarios en LineageOS.
Conservarlos requerirá revisar init, permisos, símbolos y dependencias transitivas;
el nombre OEM por sí solo no justifica incluirlos.

## Correcciones del analizador

`tools/elf_deps.py` ya no considera una allowlist de nombres AOSP como proveedores
verificados. Solo muestra candidatos ELF64 de la misma arquitectura y registra
los nombres de plataforma como pendientes. Excluye objetos ET_REL y ejecutables
sin identidad de biblioteca de la lista de proveedores. Informa errores,
formatos no soportados y symlinks no seguidos. Valida límites de las tablas y
cadenas para no aceptar strings fuera de DT_STRSZ ni tablas dinámicas truncadas.

El resultado es cobertura de nombres, no resolución del linker. Todavía falta
validar símbolos/versiones, rutas y namespaces, aliases, APEX/APK y dlopen.
AOSP explica esta distinción en [linker namespaces](https://source.android.com/docs/core/architecture/vndk/linker-namespace).
El `ld.config.txt` vivo se conservó localmente como evidencia; no se instala en la ROM.

## Reproducir

La raíz debe contener `vendor/`, `odm/`, `system_ext/` y `product/` extraídos
con sus rutas originales. Guardar los resultados completos fuera del repositorio:

```sh
python3 tools/tests/test_elf_deps.py
python3 tools/elf_deps.py /ruta/dump --report /ruta/informes/elf-report.json
python3 tools/summarize_elf_audit.py /ruta/informes/elf-report.json /ruta/informes/elf-triage.json
```

`elf_deps.py` devuelve error si hubo fallos de lectura/parseo. Un retorno cero
no significa que estén resueltas todas las dependencias; consultar `unresolved`,
`unsupported_elf` y los límites del informe. El resumen omite la ruta local raíz.

## Siguiente integración

1. Revisar APK/APEX/overlays y los ELF32; seleccionar los servicios realmente
   necesarios y sus proveedores según la rama LineageOS elegida.
2. Resolver símbolos, namespaces y librerías aportadas por código fuente antes de
   convertir candidatos en `proprietary-files.txt`. El inventario original de
   3718 candidatos se conserva; el nuevo inventario no se agrega a ciegas.
3. Auditar KMI, HALs/VINTF, init, SEPolicy, AVB y OTA. Mantener la configuración
   de bring-up bloqueada hasta resolverlos. No se ejecutó una compilación.
