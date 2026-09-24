#!/usr/bin/env python3
"""Stage a private, hash-checked stock kernel provider; never build or flash it.

Requires lz4 and already extracted stock inputs. Creates a new directory only.
On failure a partial directory is retained for inspection, never deleted/reused.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
from audit_kernel_modules import cpio_entries


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('reference', 'boot_unpacked', 'vendor_boot_unpacked', 'dtbo',
                 'dlkm_root', 'vendor_ifas', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('destination exists; refuse to overwrite or reuse it')
    reference_bytes = args.reference.read_bytes().replace(b'\r\n', b'\n')
    ref = json.loads(reference_bytes)
    if ref['device'] != 'NX733J' or ref['provider_kind'] != 'stock_prebuilt':
        raise ValueError('requires NX733J stock reference')
    artifact_sources = {
        'kernel': args.boot_unpacked / 'kernel',
        'dtb': args.vendor_boot_unpacked / 'dtb',
        'dtbo_reference': args.dtbo,
        'vendor_ramdisk_reference': args.vendor_boot_unpacked / 'vendor_ramdisk00',
        'bootconfig_reference': args.vendor_boot_unpacked / 'bootconfig',
    }
    if {r['role'] for r in ref['artifacts']} != set(artifact_sources):
        raise ValueError('unsupported reference artifact roles')
    for row in ref['artifacts']:
        data = artifact_sources[row['role']].read_bytes()
        if len(data) != row['bytes'] or sha(data) != row['sha256']:
            raise ValueError('artifact differs from stock reference: ' + row['role'])
    args.output.mkdir(parents=True, exist_ok=False)
    output = args.output.resolve()
    records = {}

    def add(relative, data, kind, expected=None):
        name = PurePosixPath(relative)
        if name.is_absolute() or '..' in name.parts or '\\' in relative:
            raise ValueError('unsafe output path')
        if relative in records:
            raise ValueError('duplicate output path: ' + relative)
        digest = sha(data)
        if expected is not None and digest != expected:
            raise ValueError('input hash mismatch: ' + relative)
        target = output.joinpath(*name.parts)
        if not target.resolve().is_relative_to(output):
            raise ValueError('output path escapes provider directory')
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
        if sha(target.read_bytes()) != digest:
            raise ValueError('copied bytes failed verification: ' + relative)
        records[relative] = {'path': relative, 'kind': kind, 'bytes': len(data), 'sha256': digest}

    for row in ref['artifacts']:
        add(row['path'], artifact_sources[row['role']].read_bytes(), 'artifact', row['sha256'])
    expected = {row['path']: row for row in ref['modules']}
    if len(expected) != len(ref['modules']):
        raise ValueError('duplicate module reference paths')
    seen = set()

    def add_module(path, data):
        if path not in expected or path in seen:
            raise ValueError('unexpected or duplicate module: ' + path)
        add(path, data, 'module', expected[path]['sha256'])
        seen.add(path)

    ramdisk = subprocess.check_output(['lz4', '-dc', str(artifact_sources['vendor_ramdisk_reference'])])
    for name, data in cpio_entries(ramdisk):
        if name.endswith('.ko'):
            add_module('modules/vendor_boot/' + name, data)
        elif name.startswith('lib/modules/modules.'):
            add('modules/vendor_boot/' + name, data, 'load_metadata')
    for partition in ('vendor_dlkm', 'system_dlkm'):
        root = args.dlkm_root / partition
        for path in sorted(root.rglob('*')):
            if path.is_symlink():
                raise ValueError('unexpected symlink in extracted DLKM input: ' + str(path))
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            if relative.endswith('.ko'):
                add_module('modules/' + partition + '/' + relative, path.read_bytes())
            elif relative.startswith('lib/modules/'):
                add('modules/' + partition + '/' + relative, path.read_bytes(), 'load_metadata')
            else:
                add('reference/partitions/' + partition + '/' + relative, path.read_bytes(), 'partition_reference')
    add_module('modules/vendor/ifas.ko', args.vendor_ifas.read_bytes())
    if seen != set(expected):
        raise ValueError('reference modules missing from inputs')
    for row in ref['load_lists']:
        source = args.reference.parent.parent / row['source']
        data = source.read_bytes().replace(b'\r\n', b'\n')
        add('reference/' + source.name, data, 'load_list_reference', row['sha256_lf'])
    add('reference/stock-provider-reference.json', reference_bytes, 'reference_manifest')
    report = {
        'schema_version': 1, 'device': 'NX733J', 'provider_kind': 'stock_prebuilt',
        'status': 'STAGED_NOT_BUILD_INTEGRATED',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'reference_sha256_lf': sha(reference_bytes), 'kernel_release': ref['kernel_release'],
        'verified_module_files': len(seen), 'verified_output_files': len(records),
        'payload_bytes': sum(row['bytes'] for row in records.values()),
        'counts_by_kind': dict(Counter(row['kind'] for row in records.values())),
        'files': [records[k] for k in sorted(records)],
        'limits': ['Private staging only; no build variables or product copies are enabled.',
                   'File hashes do not establish complete kernel ABI, signature policy or flash safety.',
                   'Original load metadata and partition properties are reference inputs, not ROM integration decisions.',
                   'This is not a complete filesystem image; ownership, labels and image signing still belong to ROM integration.'],
    }
    with (output / 'provider-manifest.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('files', 'limits')}, indent=2))


if __name__ == '__main__':
    main()
