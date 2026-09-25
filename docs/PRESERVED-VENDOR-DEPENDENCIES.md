# Dependencias de vendor conservado: primera delimitación

Fecha: 2026-09-25. Alcance: referencias ELF ya auditadas y declaraciones de
servicios de vendor; no se portaron subsistemas de hardware.

## ELF: no duplicar proveedores por coincidencia de nombre

La auditoría previa de 2393 ELF registró 103 nombres usados desde vendor/odm con
candidatos en system_ext/product. Todos tenían también candidatos en vendor/odm.
Esto no obliga a extraer 103 bibliotecas externas ni demuestra qué variante
resolverá el linker. Los 81 nombres sin proveedor en las cuatro particiones
incluyen proveedores de system/APEX: continúan pendientes símbolos y namespaces.
Véase [ELF-AUDIT](ELF-AUDIT.md). No se cambió proprietary-files.txt.

## Init: declaraciones frente a observación

[Inventario](../stock/preserved-init-refs.json): 154 archivos rc de vendor
examinados, 28 declaraciones con ejecutable o argumento literal fuera de vendor,
30 declaraciones mediante `/system/vendor`. No hubo errores del lector acotado.
No se interpreta el grafo de imports, triggers, overrides ni scripts completos.

[Observación ADB](../stock/preserved-init-live.json), slot B, sin cambio de boot:

- `/system/vendor` apunta a `/vendor`; esas 30 referencias no se clasifican como
  paquetes de system que haya que copiar.
- De 28 nombres consultados, sólo repeater_tune y usbconfig devolvieron estado,
  ambos stopped. La ausencia de propiedad no prueba que una declaración nunca
  se registre o que sea innecesaria en otra fase.
- De 18 rutas literales consultadas, siete devolvieron tipo regular file y once
  fallaron stat. Las siete son bootanimation, diag_socket_log.sh, dumpstate,
  init.vendor.usb.sh, sh, usbconfig y system_ext/bin/tcpcat.
- Presencia en disco y estado por nombre no atribuyen una declaración concreta
  cuando puede haber duplicados/override, ni prueban uso durante el arranque.

La captura publicada usa `adb shell -T`, códigos de salida remotos y tipos de
archivo validados. Una captura local preliminar con exec-out clasificaba mal los
fallos stat a partir del retorno del transporte; se corrigió y repitió antes de
publicar. No se inició ni detuvo ningún servicio.

## Consecuencia para el perfil inicial

No aprobar archivos nuevos por la sola aparición de una ruta en rc. Primero
resolver la ruta de importación y la necesidad de la función en la ROM. Conservar
vendor mantiene sus declaraciones: las dependencias usadas deberán ser aportadas
por fuentes ROM, un port documentado o blobs revisados con sus reglas SELinux.

bootservice/ssdaemon/vendorcfg y libvendorcfg.oem.so continúan como decisiones
OEM abiertas; no se añaden para compensar indiscriminadamente referencias antiguas.
No se estudió todavía la implementación de cámara/audio/NFC ni otros subsistemas.

Siguiente revisión acotada: cadena de imports del init principal y de los
servicios USB mencionados, para determinar qué requiere realmente el primer
arranque con ADB. El contenido de scripts y símbolos sigue sin aprobarse.

## Reproducción

```text
python tools/audit_preserved_init_refs.py <vendor-extraido> <informe-nuevo.json>
python tools/capture_preserved_init_state.py <informe.json> <captura-nueva.json> --adb <adb>
```

La primera herramienta no sigue symlinks rc. Ambas rechazan destinos existentes.
La segunda consulta sólo estados y metadatos de las rutas seleccionadas.
