#!/usr/bin/env python3
"""Capture exported symbol names/owners using read-only adb root commands.

Does not change kernel settings, expose addresses in the output or load modules.
Requires an already connected device and working su authorization.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--adb', default='adb')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; use a new capture path')

    def read(command):
        return subprocess.check_output(
            [args.adb, 'exec-out', "su -c '" + command + "'"],
            timeout=60, encoding='utf-8')

    kernel = read('uname -r').strip()
    slot = read('getprop ro.boot.slot_suffix').strip()
    exports = {}
    for line in read('cat /proc/kallsyms').splitlines():
        fields = line.split()
        if len(fields) < 3 or not fields[2].startswith('__ksymtab_'):
            continue
        symbol = fields[2][len('__ksymtab_'):]
        owner = fields[3].strip('[]') if len(fields) > 3 else 'kernel'
        exports.setdefault(symbol, []).append(owner)
    if not exports:
        raise ValueError('no export names available; do not treat this as an empty kernel')
    if read('uname -r').strip() != kernel or read('getprop ro.boot.slot_suffix').strip() != slot:
        raise ValueError('kernel or slot changed during capture')
    report = {
        'captured_utc': datetime.now(timezone.utc).isoformat(),
        'kernel': kernel, 'slot': slot, 'exports': exports,
        'limits': ['Addresses discarded; these are symbol names, not CRC values.',
                   'Loaded owner names do not identify exact loaded bytes.',
                   'This is a runtime observation, not an atomic module-load trace.'],
    }
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print('Captured export names:', len(exports))


if __name__ == '__main__':
    main()
