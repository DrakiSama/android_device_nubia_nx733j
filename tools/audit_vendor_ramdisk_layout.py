#!/usr/bin/env python3
"""Inventory stock vendor ramdisk ownership and first-stage fstab, read-only."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import stat
import subprocess


def sha(data):
    return hashlib.sha256(data).hexdigest()


def records(data):
    offset = 0
    seen = set()
    while offset + 110 <= len(data):
        h = data[offset:offset + 110]
        if h[:6] != b'070701':
            raise ValueError('requires newc CPIO without checksum')
        f = [int(h[6 + i * 8:14 + i * 8], 16) for i in range(13)]
        size, namesize = f[6], f[11]
        offset += 110
        if namesize < 1 or offset + namesize > len(data):
            raise ValueError('invalid name size')
        name = data[offset:offset + namesize]
        if name[-1:] != b'\0':
            raise ValueError('unterminated name')
        name = name[:-1].decode('utf-8')
        offset = (offset + namesize + 3) & ~3
        body = data[offset:offset + size]
        if len(body) != size:
            raise ValueError('truncated entry')
        offset = (offset + size + 3) & ~3
        if name == 'TRAILER!!!':
            if size or any(data[offset:]):
                raise ValueError('unexpected trailer data')
            return
        if name in seen:
            raise ValueError('duplicate path: ' + name)
        seen.add(name)
        yield {'path': name, 'mode': oct(f[1]), 'uid': f[2], 'gid': f[3],
               'nlink': f[4], 'bytes': size, 'sha256': sha(body),
               'type': 'regular' if stat.S_ISREG(f[1]) else 'directory' if stat.S_ISDIR(f[1]) else 'other'}, body
    raise ValueError('missing CPIO trailer')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('ramdisk', 'reference', 'fstab', 'output'):
        p.add_argument(name, type=Path)
    args = p.parse_args()
    if args.output.exists():
        p.error('output exists; refuse overwrite')
    ref_bytes = args.reference.read_bytes().replace(b'\r\n', b'\n')
    ref = json.loads(ref_bytes)
    if ref['device'] != 'NX733J':
        raise ValueError('requires NX733J reference')
    artifact = [r for r in ref['artifacts'] if r['role'] == 'vendor_ramdisk_reference']
    compressed = args.ramdisk.read_bytes()
    if len(artifact) != 1 or sha(compressed) != artifact[0]['sha256'] or len(compressed) != artifact[0]['bytes']:
        raise ValueError('ramdisk differs from stock reference')
    data = subprocess.check_output(['lz4', '-dc', str(args.ramdisk)])
    module_ref = {r['path'].removeprefix('modules/vendor_boot/'): r for r in ref['modules']
                  if r['path'].startswith('modules/vendor_boot/')}
    nonmodules, modules, rows = [], [], []
    fstab_hash = None
    for row, body in records(data):
        if row['path'].endswith('.ko'):
            expected = module_ref.get(row['path'])
            if expected is None or row['sha256'] != expected['sha256']:
                raise ValueError('module differs from reference: ' + row['path'])
            modules.append(row)
        else:
            nonmodules.append(row)
        if row['path'] == 'first_stage_ramdisk/fstab.qcom':
            if body.replace(b'\r\n', b'\n') != args.fstab.read_bytes().replace(b'\r\n', b'\n'):
                raise ValueError('published fstab differs from ramdisk')
            fstab_hash = sha(body)
            for number, line in enumerate(body.decode('utf-8').splitlines(), 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                fields = line.split()
                if len(fields) != 5:
                    raise ValueError('unexpected fstab fields at line ' + str(number))
                source, mount, fs, options, flags = fields
                rows.append({'line': number, 'source': source, 'mount_point': mount,
                             'filesystem': fs, 'mount_options': options.split(','),
                             'fs_mgr_flags': flags.split(',')})
    if fstab_hash is None or {r['path'] for r in modules} != set(module_ref):
        raise ValueError('missing fstab or modules')
    permissions = Counter((r['mode'], r['uid'], r['gid'], r['nlink']) for r in modules)
    report = {'schema_version': 1, 'created_utc': datetime.now(timezone.utc).isoformat(),
              'device': 'NX733J', 'ramdisk_sha256': sha(compressed),
              'reference_sha256_lf': sha(ref_bytes), 'cpio_sha256': sha(data),
              'nonmodule_entries': nonmodules, 'module_count': len(modules),
              'all_module_hashes_match_reference': True,
              'module_permissions': [{'mode': k[0], 'uid': k[1], 'gid': k[2], 'nlink': k[3], 'count': v}
                                     for k, v in sorted(permissions.items())],
              'fstab_sha256': fstab_hash, 'fstab_matches_published_lf': True, 'fstab_entries': rows,
              'limits': ['newc does not encode SELinux xattrs; runtime labels not proven',
                         'fstab presence does not prove every entry is exercised',
                         'No ramdisk, mount, format or filesystem changes']}
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'module_count': len(modules), 'nonmodule_count': len(nonmodules),
                      'fstab_entries': len(rows), 'first_stage_entries': sum('first_stage_mount' in r['fs_mgr_flags'] for r in rows),
                      'module_permissions': report['module_permissions']}))


if __name__ == '__main__':
    main()
