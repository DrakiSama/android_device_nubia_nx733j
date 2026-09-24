# Contrato del proveedor de kernel NX733J

Estado: diseño de integración; no activa un build. Referencia inicial stock/prebuilt.
Las decisiones de arquitectura siguientes son propuestas del proyecto, no hechos
extraídos del firmware. Los hechos stock llevan CONFIRMED y procedencia explícita.

## Frontera de responsabilidades

| Responsable | Entradas / salidas | Límite |
| --- | --- | --- |
| Proveedor de kernel | Image ARM64, módulos por partición, identidad/configuración, evidencia ABI y firmas | Puede usar prebuilts o producir salidas desde fuentes |
| Plataforma NX733J | DTB/DTBO propios, tamaños, fstab, política de carga y dependencias tempranas | Otro SM8750 no sustituye esta evidencia |
| Integración ROM | Ramdisk genérico init_boot, init/SELinux, construcción de imágenes, AVB y OTA | No hereda el init parcheado ni las claves stock |

El DTB/DTBO de referencia se registra junto al kernel para controlar compatibilidad,
aunque corresponde al hardware NX733J. Cambiar el proveedor no obliga a copiar
el device tree ni a mezclar sus makefiles con los de un repositorio de kernel.
Una futura implementación debe depender de archivos de salida explícitos: recompilar
solo las imágenes afectadas, según el grafo de dependencias del build elegido.
Esto es un requisito de diseño; aún no existe ese adaptador de build.

## Entradas concretas de la referencia stock

[CONFIRMED] Los hashes y tamaños se registran en
[kernel-provider-reference.json](../stock/kernel-provider-reference.json).
Las rutas definen el directorio privado del proveedor; no contienen
binarios en Git. Los hashes stock se exigen únicamente al proveedor stock de esta
captura. Un proveedor custom/source tendrá su propio manifiesto y validación.

| Ruta conceptual | Origen verificado | Uso previsto |
| --- | --- | --- |
| kernel/Image | Payload de boot B; ARM64 sin compresión; 36596224 bytes | Kernel de boot |
| dtb/dtb.img | vendor_boot B; 4487979 bytes | DTB NX733J; no elegir otro dispositivo |
| dtbo/dtbo.img | Captura completa de dtbo B; 37 entradas | Referencia completa; conservar selección de variantes |
| reference/vendor_ramdisk00 | Fragmento PLATFORM de vendor_boot B | Referencia para reconstrucción; no reemplazo ciego del ramdisk ROM |
| reference/bootconfig | 232 bytes de vendor_boot B | Parámetros OEM por revisar en la integración |
| modules/vendor_boot/lib/modules/* | 306 archivos del ramdisk | Candidatos para carga temprana y recovery, con listas distintas |
| modules/system_dlkm/lib/modules/* | 94 archivos de system_dlkm B | Conservar identidad y firmas de cada módulo |
| modules/vendor_dlkm/lib/modules/* | 280 archivos de vendor_dlkm B | Preservar listas, dependencias y filtros stock como evidencia |
| modules/vendor/ifas.ko | vendor B | Módulo OEM tardío; inventariado, inclusión pendiente |

La ruta dtbo representa la partición completa: payload, contenedor AVB interno
y ceros finales;
no confundir sus 25165824 bytes con los 14124069 bytes usados por la tabla.
Los directorios modules/vendor_boot son nombres del inventario, no puntos de
montaje Android. Las rutas concretas se enumeran individualmente en el manifiesto.

## Mapa de carga observado

| Momento / partición | CONFIRMED | Decisión pendiente |
| --- | --- | --- |
| Vendor ramdisk, arranque normal | modules.load.boot: 106 entradas; cierre modinfo y de símbolos dentro del ramdisk/kernel | Revisar softdeps, alias y orden temporal antes de integrar |
| Vendor ramdisk, recovery | 303 entradas; cierre incluye dependencia hdcp_qseecom_dlkm | Mantener lista independiente; no usarla para arranque normal |
| Segunda etapa init, system_dlkm | early-init ejecuta gki.modprobe; script enumera .ko y aplica blocklist | Reproducir necesidades con init/SELinux propios; lista vacía no significa ausencia de carga |
| Segunda etapa init, vendor_dlkm | vendor.modprobe se inicia tras exec_start gki.modprobe; procesa modules.load y filtros | Respeta dependencias y módulos excluidos; el script lanza cargas en paralelo |
| Vendor / ifas | init.zte.perf.rc declara insmod /vendor/ifas.ko | Mantener fuera de carga temprana; necesidad para bring-up no demostrada |

[CONFIRMED] zram/zsmalloc cargados tienen los build IDs de vendor_boot 6.6.30,
con kernel stock 6.6.92. Las variantes system_dlkm son distintas. Conservar ambas
por partición; no sustituir por la de mayor vermagic. La observación no identifica
la secuencia completa de inserción ni garantiza compatibilidad con otro kernel.

## Condiciones para sustituir el proveedor

1. Identificar fuentes o prebuilts, versión, configuración y procedencia de cada
   artefacto, con SHA-256; nunca mezclar slots/versiones sin comprobarlos.
2. Contrastar imports/exportaciones, valores CRC y namespaces contra el kernel
   elegido, además de configuración, CFI y política de firmas. Una coincidencia
   de nombres o vermagic no basta. Para kernel source, conservar Module.symvers,
   configuración, herramientas y resultados ABI de esa compilación exacta.
3. Resolver DTB/DTBO y módulos como conjunto compatible; permitir reutilizar un
   componente sin recompilarlo cuando exista evidencia suficiente de compatibilidad.
4. Mantener las listas normal/recovery separadas y las dependencias de primera
   etapa disponibles antes de montar DLKM. No suponer cierre temporal a partir
   de /proc/modules capturado después de arrancar.
5. Reconstruir init_boot desde la ROM; preservar el init_boot stock limpio solo
   como referencia. AVB, rollback, pvmfw y alcance OTA son decisiones separadas.
6. Habilitar construcción de imágenes solo tras cerrar los bloqueos de
   [BRINGUP_STATUS](BRINGUP_STATUS.md). La vía de recuperación se confirma antes
   de cualquier escritura al dispositivo.

## Lo que este contrato no demuestra

La referencia stock no certifica la ABI de un kernel recompilado. La información
runtime corresponde a un teléfono con root. Aún faltan los valores de exportaciones
CRC del kernel contrastados contra los imports, namespaces y política de firmas.
La ausencia deliberada de BoardConfigBringup.mk se conserva; este contrato no añade
variables de build ficticias, no instala módulos y no contiene comandos de flasheo.

El [análisis de símbolos y CRC](MODULE-EXPORT-CRC.md) documenta el cierre estático
del conjunto normal. No implica validación temporal de la carga en paralelo.

La [auditoría de carga normal](RAMDISK-LOAD-AUDIT.md) confirma el cierre con
softdeps y los 106 build IDs observados; conserva pendiente la secuencia temporal.

El [paquete stock privado](KERNEL-PROVIDER-PACKAGE.md) ya se preparó y verificó
contra este contrato. Su integración con el build permanece pendiente.
