#!/usr/bin/env python3
"""Capture selected stock init service states and path metadata via ADB shell v2.

Does not read file contents or start/stop services. Requires authorized root ADB.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('references', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--adb', default='adb')
    a = p.parse_args()
    if a.output.exists():
        p.error('output exists; refuse overwrite')
    raw = a.references.read_bytes().replace(b'\r\n', b'\n')
    ref = json.loads(raw)
    if ref['parse_limits_or_errors']:
        p.error('resolve reference parsing errors first')

    def query(command):
        # shell -T retains the remote exit status; exec-out must not be used
        # to classify stat success from its host exit code alone.
        return subprocess.run([a.adb, 'shell', '-T', "su -c '" + command + "'"],
                              capture_output=True, timeout=15)

    def read(command):
        result = query(command)
        if result.returncode:
            raise ValueError('device query failed: ' + command)
        return result.stdout.decode('utf-8').strip()

    before = read('cat /proc/sys/kernel/random/boot_id')
    if not re.fullmatch(r'[0-9a-f-]{36}', before):
        raise ValueError('invalid boot identity')
    slot = read('getprop ro.boot.slot_suffix')
    names = sorted({r['service'] for r in ref['external_service_declarations']})
    paths = sorted({r['executable'] for r in ref['external_service_declarations']} |
                   {x for r in ref['external_service_declarations'] for x in r['literal_external_arguments']})
    states, files = {}, {}
    for name in names:
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', name):
            raise ValueError('nonliteral service name')
        value = read('getprop init.svc.' + name)
        if value not in ('', 'running', 'stopped', 'stopping', 'restarting'):
            raise ValueError('unexpected service state')
        states[name] = value or None
    for path in paths:
        if not re.fullmatch(r'/[A-Za-z0-9_./-]+', path):
            raise ValueError('nonliteral target path')
        result = query('stat -L -c %F ' + path)
        value = result.stdout.decode('utf-8').strip()
        valid = result.returncode == 0 and value in ('regular file', 'directory', 'symbolic link',
                'character special file', 'block special file', 'fifo', 'socket')
        if result.returncode == 0 and not valid:
            raise ValueError('stat did not return a recognized type: ' + path)
        files[path] = {'stat_succeeded': valid, 'remote_exit_code': result.returncode,
                       'file_type': value if valid else None}
    alias = read('readlink /system/vendor')
    if before != read('cat /proc/sys/kernel/random/boot_id'):
        raise ValueError('boot changed during capture')
    report = {'captured_utc': datetime.now(timezone.utc).isoformat(), 'slot': slot,
              'same_boot_during_capture': True, 'references_sha256_lf': hashlib.sha256(raw).hexdigest(),
              'transport': 'adb shell -T with remote exit codes and validated output',
              'system_vendor_symlink_target': alias, 'service_states': states, 'path_observations': files,
              'limits': ['Service-name state does not identify a particular duplicate/override declaration',
                         'Missing state or failed stat is not proof a component is unnecessary for ROM',
                         'No service started/stopped; no file contents read']}
    with a.output.open('x', encoding='utf-8', newline='\n') as out:
        json.dump(report, out, indent=2)
        out.write('\n')
    print(json.dumps({'service_names': len(states), 'states_observed': sum(v is not None for v in states.values()),
                      'paths': len(files), 'stat_succeeded': sum(v['stat_succeeded'] for v in files.values()),
                      'system_vendor_alias': alias}))


if __name__ == '__main__':
    main()
