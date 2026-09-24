# Estado observado de snapshots y mapas NX733J

Fecha: 2026-09-24; slot B. Consulta de solo lectura de las siete particiones
lógicas del sistema, sus siete mapas COW y sus siete mapas verity. No se consultó
la tabla de userdata ni se ejecutó actualización, merge, cancelación o cambio de slot.

## Confirmado en esta captura

- Los 21 mapas consultados usan únicamente targets linear o verity; no aparece
  snapshot, snapshot-merge ni user en esas tablas.
- Los siete mapas base B y los siete mapas COW coinciden, extent por extent y por
  tamaño, con el juego de metadatos 1 del super del respaldo ya auditado.
- El dispositivo físico 8:7 corresponde a /dev/block/sda7, partición super,
  comprobado mediante el enlace by-name y sysfs en este arranque. No es una ruta
  que deba fijarse por nombre sda7 para otros dispositivos o modos de arranque.
- Las siete raíces, salts, algoritmos y tamaños de datos verity coinciden con los
  descriptores stock B de vbmeta/vbmeta_system.
- /metadata/ota/snapshots está vacío y /metadata/ota/state tiene cero bytes.
- update_engine_client --follow informó UPDATE_STATUS_IDLE (0), progreso 0;
  el cliente finalizó con código 0 dentro del límite de cinco segundos.

Conclusión acotada: no se observa snapshot/merge activo en los mapas consultados
y el servicio de actualización se declara inactivo en esta captura. Las reservas
con nombres *-cow siguen mapeadas como linear. Sus nombres no prueban un merge
activo ni autorizan eliminar o reutilizar esas reservas.

## Evidencia

- [Mapas vivos frente al respaldo y descriptores](../stock/snapshot-runtime-audit.json).
- [Estado comunicado por update_engine](../stock/update-engine-observation.json).

Se usaron dmctl list devices, dmctl table/status sobre los nombres seleccionados,
lecturas de metadata, y una suscripción acotada al estado de update_engine:

```sh
adb shell "su -c 'timeout -k 2 5 update_engine_client --follow'"
```

Los scripts locales capture-snapshot-state.py y compare-live-maps.py y sus tablas
originales permanecen en diagnostics/edl-backup-20260504-audit. La comparación usa
los extents ya registrados y las salidas de avbtool del respaldo. La consulta del
servicio se guardó aparte. No se extrajo otra imagen completa de super.

## Límites

No se llamó directamente a una API de libsnapshot para obtener su enum interno;
snapshotctl no está disponible. El resultado de dumpsys del servicio estaba vacío:
no se utilizó esa ausencia como prueba de inactividad. El callback posterior es la
evidencia del estado de update_engine.

Las lecturas describen este arranque, no una futura OTA. No prueban una vía segura
de restauración ni validan la confianza OEM, rollback o corrección de FEC. Las
entradas COW y las copias históricas de metadatos del respaldo se conservan intactas.
