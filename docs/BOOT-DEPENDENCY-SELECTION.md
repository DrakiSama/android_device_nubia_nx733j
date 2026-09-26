# Selección mínima de dependencias externas: primer arranque

Fecha: 2026-09-26. Estado: primera selección completada para el alcance "primer
arranque diagnosticable con ADB" del perfil preservado. No se extrajo, copió ni
aprobó ningún blob; no se creó `proprietary-files.txt`.

## Alcance y fuentes

Perfil stock B: vendor/odm/vendor_dlkm/system_dlkm preservados; system,
system_ext y product reconstruidos desde fuentes. Esta selección responde solo
a la pregunta: ¿qué archivos OEM externos necesita la ROM para arrancar hasta
ADB? El hardware (Wi-Fi, audio, cámara…) se difiere por subsistema.

Fuentes: `stock/preserved-init-refs.json` (154 rc vendor), `stock/preserved-init-live.json`,
`stock/elf-audit.json`, [ELF-AUDIT](ELF-AUDIT.md), `stock/system-ext-product-inventory.txt`
y la extracción auditada del 2026-09-23 (`diagnostics/rom-audit-2026-09-23/`).

## Referencias init externas (28 declaraciones)

Todas las declaraciones con ejecutable fuera de vendor, clasificadas:

| Grupo | Nº | Decisión para el primer arranque | Razón |
| --- | ---: | --- | --- |
| Cubiertos por fuente LineageOS: `bootanimation` (shutdownanim), `dumpstate` (bugreport ×2), `sh` (qti-testscripts) | 4 | aportar desde fuente | componentes AOSP compilados en la ROM; el script de testscripts es de prueba y su servicio está `disabled` |
| `dhcpcd` (10 servicios late_start `disabled`) | 10 | diferir a la fase Wi-Fi | AOSP retiró dhcpcd; el binario stock es OEM; no interviene en ADB |
| Herramientas OEM de diagnóstico/fábrica/test: `qmiproxy`, `qlogd`, `mmi`, `mmi_diag`, `tcpip_attach_detach` (×2), `tcpcat`, `diag_socket_log.sh`, `move_wifi_data.sh`, `battery_monitor`, `profiler_daemon`, `alikey_client` | 12 | omitir por ahora | servicios `disabled` o de fábrica; sin consumidor en el primer arranque |
| `init.vendor.usb.sh` (repeater_tune) | 1 | diferir con ruido documentado | se dispara si `persist.sys.usb.default` está vacío; no configura ADB/FunctionFS; sin él solo queda sin fijar esa propiedad |
| `usbconfig` | 1 | excluido (decisión propuesta) | helper de fábrica inoperante en este kernel; ver [USBCONFIG-ANALYSIS](USBCONFIG-ANALYSIS.md) |
| **Total** | **28** | | |

Las 30 declaraciones mediante `/system/vendor/...` no son paquetes externos:
`/system/vendor` apunta a `/vendor` (preservado); CONFIRMADO en la observación
viva.

## Dependencias ELF

- 81 nombres DT_NEEDED sin proveedor en las cuatro particiones: sus candidatos
  están en `/system/lib64` o `/apex` → los aporta la fuente de la ROM, no son
  blobs.
- 103 nombres usados desde vendor/odm con candidatos también en
  system_ext/product: todos tienen además candidatos en vendor/odm (preservado);
  no hay evidencia para copiar las variantes de system_ext. Símbolos, versiones
  y namespaces siguen pendientes (fase VINTF/linker).
- Caso `libvendorcfg.oem.so` (servicios `bootservice`, `ssdaemon`, `vendorcfg`
  de system_ext): decisión diferida; no es primer arranque.

Conclusión: **cero extracciones ELF nuevas** para el primer arranque.

## Contenido OEM de system_ext/product

- 2621 archivos inventariados; 29 rc de init; un manifest VINTF.
- `system_ext/etc/vintf/manifest.xml` es contenido **AOSP por defecto**
  (`system_ext_manifest.default.xml` + `hwservicemanager.xml`: declara
  `android.hidl.manager@1.2` y `android.hidl.token@1.0`). La ROM lo regenera
  desde fuente; sin acción.
- `product/etc/vintf/manifest/vendor.qti.qvirt-service.xml`: servicio de
  virtualización QTI; diferido.
- Los 29 rc pertenecen a servicios OEM/QTI que no se instalan al reconstruir
  desde fuente (`bootservice`, `ssdaemon`, `vendorcfgd`, `logcontrol`, `getlog`,
  `qsguard`, `qspa_system`, `qspmsvc`, `tcmd`, `usbudev`, `dpmd`, `ebase`,
  `SpaceScan`, `sigma_miracast`, `wfdservice`, `qccsyshal`, `perfservice`,
  `boot_rescue`, `connectivity`, `hwservicemanager` OEM, qvirt…). Se revisan
  por subsistema si se portan.

## Consecuencia para el generador y el primer build

- La lista de dependencias externas para las particiones reconstruidas es
  **vacía en el primer arranque**: base LineageOS + imágenes preservadas +
  proveedor kernel stock.
- El modo acotado del generador (frontera documentada en
  [PRESERVED-PROFILE-INTEGRATION](PRESERVED-PROFILE-INTEGRATION.md)) puede
  arrancar con un manifiesto sin entradas vendor/odm/dlkm ni system_ext/product,
  y crecer por subsistema con evidencia; este documento es el punto de partida.
- No se creó el manifiesto ni se modificó `extract-files.py`.

## Riesgos y límites

- Es una selección de primer arranque, no de hardware: Wi-Fi/BT/audio/cámara
  traerán dependencias nuevas (la primera será `dhcpcd` en Wi-Fi).
- La ausencia de extracciones no equivale a compatibilidad probada: símbolos,
  namespaces y VINTF siguen pendientes.
- Los servicios `disabled` solo fallan si un trigger los arranca; el ruido de
  exec de `usbconfig` y `repeater_tune` queda documentado y no se silencia con
  archivos ficticios.
- Nada de esto se probó en ejecución.

## Reproducción

```text
# Consultas de solo lectura usadas para la clasificación
python3 -c "import json;d=json.load(open('stock/preserved-init-refs.json'));print(len(d['external_service_declarations']))"
grep -cE '/etc/init/.*\.rc$' stock/system-ext-product-inventory.txt
# Manifest de system_ext stock (extracción auditada, fuera del repo)
head -70 diagnostics/rom-audit-2026-09-23/system_ext/etc/vintf/manifest.xml
```
