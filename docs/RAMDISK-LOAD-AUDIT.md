# Auditoría de carga normal del ramdisk NX733J

Fecha: 2026-09-24. Alcance: conjunto stock de arranque normal, sin modificar listas,
cargar módulos, reiniciar servicios ni cambiar configuración del dispositivo.

## Evidencia stock confirmada

| Comprobación | Resultado |
| --- | --- |
| modules.dep | 306 entradas; todas sus referencias resuelven dentro del ramdisk |
| Lista normal | 106 módulos únicos; coincide byte a byte con stock/modules.load.boot |
| Softdeps | 14 reglas totales; 5 aplican al conjunto normal; cierre sigue siendo 106 |
| Grafo combinado | 771 restricciones; acíclico; 13 capas topológicas posibles |
| Aliases | 974 entradas, todas con destino presente; ninguna coincide con los nombres explícitos de la lista normal |
| Blocklist | 60 entradas, 59 nombres únicos; no afecta al conjunto normal |
| Build IDs en vivo | 106/106 notas GNU coinciden con los ELF stock de referencia |
| Carga paralela | ro.boot.load_modules_parallel=true en la captura actual |

Las cinco reglas pre activas son: qcom_pmu_lib -> qcom_scmi_client,
smem -> qcom_hwspinlock, pinctrl_msm -> qcom-pdc,
qcom_scmi_client -> qcom_scmi_vendor y sched_walt -> socinfo.
La flecha significa que el módulo de la izquierda pide cargar antes el de la derecha.

Hay 450 restricciones cuyo prerrequisito aparece después del consumidor en el
texto de modules.load. Eso no convierte la lista stock en incorrecta: requiere
que el cargador resuelva dependencias. No reemplazarlo por un bucle de insmod
que ignore modules.dep/softdep. Las 13 capas calculadas son un análisis estático,
no una nueva lista de carga ni una medición del scheduling stock.

Los 106 build IDs se leyeron de /sys/module/<nombre>/notes/.note.gnu.build-id;
el identificador de arranque, kernel y slot permanecieron iguales durante la
captura. Es identidad de compilación, no SHA-256 de todos los bytes en memoria,
ni prueba de cuándo se insertó cada módulo. No implica compatibilidad con otro kernel.

## Evidencias y repetición

- [Metadatos originales e inventario SHA-256](../stock/ramdisk-load-metadata/).
- [Grafo y reglas activas](../stock/ramdisk-load-graph.json).
- [Identidades de compilación observadas](../stock/early-module-build-ids.json).
- [Estado runtime y límites del registro](../stock/module-load-runtime.json).

Los archivos de stock son evidencia; no se instalan automáticamente en el producto.
Para repetir el grafo, sin necesidad de conectar el teléfono:

```sh
python3 tools/audit_ramdisk_load_graph.py stock/ramdisk-load-metadata stock/kernel-provider-reference.json /private/load-graph.json
```

La herramienta preserva las reglas originales, rechaza sobrescribir el informe y
reporta dependencias/aliases sin destino, bloqueos y nodos no ordenables. No simula
cada modalias de hardware ni prueba que un driver se vincule a un dispositivo.

La captura de build IDs se realizó con los scripts locales early-build-id-reference.py
y capture-early-build-ids.py, en diagnostics/edl-backup-20260504-audit. Leen el CPIO,
validan SHA-256 por módulo y comparan las notas ELF con sysfs. No están incluidos
como interfaz de captura genérica en este commit.

## Referencia de implementación, no identidad del init stock

REFERENCE: checkout local LineageOS system/core, commit
`bcb8623207cf6e7a51876a891d8b7ad3d04fd8c2`.

PURPOSE: entender cómo integrar estas reglas en la futura ROM. Los archivos
init/first_stage_init.cpp y libmodprobe/libmodprobe.cpp no tenían cambios locales.

Ese código selecciona modules.load para modo normal y modules.load.recovery para
recovery; reconoce androidboot.load_modules_parallel y resuelve dependencias duras
antes de las inserciones. InsmodWithDeps procesa las reglas softdep. La implementación
stock exacta no se identifica por compartir propiedades o formato: esta referencia
no demuestra su secuencia efectiva ni autoriza copiar el init completo.

## Pendientes concretos

El dmesg actual contiene 5251 líneas y ninguna coincide con el filtro de mensajes
de carga. El buffer puede haber sobrescrito el arranque; no se deduce ausencia de
errores. Los servicios oneshot figuran stopped y vendor.all.modules.ready=1, datos
que tampoco prueban éxito de cada inserción.

Persisten: orden temporal exacto, aliases frente a modalias reales, namespaces,
firmas y los valores CRC del kernel base. No se cambió el cargador para conseguir
registros ni se propuso un reinicio experimental.
