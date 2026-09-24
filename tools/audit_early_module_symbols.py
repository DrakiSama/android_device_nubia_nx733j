#!/usr/bin/env python3
"""Audit the static symbol-provider boundary of a stock ramdisk load list.
Does not load modules or prove their temporal ordering or kernel ABI.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from audit_kernel_modules import cpio_entries, module_metadata
from audit_module_export_crcs import exported_crcs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('ramdisk', 'reference', 'load_list', 'live_exports', 'output'):
        p.add_argument(name, type=Path)
    a = p.parse_args()
    if a.output.exists():
        p.error('output exists; choose a new report path')
    ref = json.loads(a.reference.read_text())
    expected = {r['path'][len('modules/vendor_boot/'):]: r for r in ref['modules']
                if r['path'].startswith('modules/vendor_boot/')}
    live = json.loads(a.live_exports.read_text())
    entries = list(cpio_entries(subprocess.check_output(['lz4', '-dc', str(a.ramdisk)])))
    modules = {}
    for path, data in entries:
        if not path.endswith('.ko'):
            continue
        if path not in expected or path in modules:
            raise ValueError('unexpected or repeated ramdisk module: ' + path)
        if hashlib.sha256(data).hexdigest() != expected[path]['sha256']:
            raise ValueError('module hash mismatch: ' + path)
        info, imports = module_metadata(data)
        modules[path] = {'info': info, 'imports': imports, 'exports': exported_crcs(data)}
    if set(modules) != set(expected):
        raise ValueError('missing reference ramdisk modules')
    lines = [line.strip() for line in a.load_list.read_text().splitlines()
             if line.strip() and not line.lstrip().startswith('#')]
    selected = set()
    for line in lines:
        matches = [path for path in modules if Path(path).name == line]
        if len(matches) != 1:
            raise ValueError('load entry is missing or ambiguous: ' + line)
        selected.add(matches[0])
    providers = {}
    for path in selected:
        for symbol, crc in modules[path]['exports'].items():
            providers.setdefault(symbol, []).append({'path': path, 'crc': crc})
    records = []
    missing = []
    crc_conflicts = []
    imported = set()
    kernel_names = set()
    ramdisk_names = set()
    for path in sorted(selected):
        dependencies = set()
        for symbol, crc in modules[path]['imports'].items():
            imported.add(symbol)
            if 'kernel' in live['exports'].get(symbol, []):
                kernel_names.add(symbol)
                continue
            candidates = providers.get(symbol, [])
            if not candidates:
                missing.append({'consumer': path, 'symbol': symbol,
                    'other_ramdisk_providers': sorted(q for q, m in modules.items()
                        if q not in selected and symbol in m['exports'])})
                continue
            ramdisk_names.add(symbol)
            if any(r['crc'] != crc for r in candidates):
                crc_conflicts.append({'consumer': path, 'symbol': symbol})
            dependencies.update(r['path'] for r in candidates if r['path'] != path)
        records.append({'path': path, 'symbol_provider_dependencies': sorted(dependencies)})
    report = {'schema_version': 1, 'kernel': live['kernel'],
        'live_capture_utc': live['captured_utc'],
        'load_list_sha256_lf': hashlib.sha256(a.load_list.read_bytes().replace(b'\r\n', b'\n')).hexdigest(),
        'list_entries': len(lines), 'unique_selected_modules': len(selected),
        'unique_import_names': len(imported), 'kernel_provider_names': len(kernel_names),
        'selected_ramdisk_provider_names': len(ramdisk_names),
        'imports_without_provider_in_selected_set_or_kernel': missing,
        'module_crc_conflicts': crc_conflicts, 'modules': records,
        'limits': ['Static symbol-provider closure only; parallel scheduling and softdeps not validated.',
                   'Kernel export names are observed but their CRC values remain unchecked.',
                   'Only __versions imports are checked, not every undefined ELF symbol.',
                   'Runtime exports do not certify acceptance of signatures, licenses or namespaces.']}
    with a.output.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(report, f, indent=2)
        f.write('\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('modules', 'limits')}, indent=2))
    if missing or crc_conflicts:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
