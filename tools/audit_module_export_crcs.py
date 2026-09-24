#!/usr/bin/env python3
"""Read-only comparison of stock module import CRCs against module exports.

Requires lz4 and the existing audit_kernel_modules parser. Never loads modules.
The live JSON is an address-free capture of __ksymtab names -> owner lists.
This does not obtain or validate the base kernel's export CRCs.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import struct
import subprocess

from audit_kernel_modules import cpio_entries, module_metadata


def exported_crcs(data):
    # module_metadata also checks the ELF class, endian, architecture and type.
    module_metadata(data)
    table = struct.unpack_from('<Q', data, 40)[0]
    stride, count, names_index = struct.unpack_from('<HHH', data, 58)
    sections = [struct.unpack_from('<IIQQQQIIQQ', data, table + i * stride)
                for i in range(count)]

    def contents(section):
        offset, size = section[4:6]
        if offset + size > len(data):
            raise ValueError('section outside ELF')
        return data[offset:offset + size]

    def string(strings, offset):
        end = strings.find(b'\0', offset)
        if offset >= len(strings) or end < 0:
            raise ValueError('invalid ELF string offset')
        return strings[offset:end].decode('utf-8')

    names = contents(sections[names_index])
    section_names = [string(names, section[0]) for section in sections]
    crc_sections = {i for i, name in enumerate(section_names)
                    if name in ('__kcrctab', '__kcrctab_gpl')}
    for section in sections:
        if section[1] in (4, 9) and section[7] in crc_sections and section[5]:
            raise ValueError('relocated CRC data requires a different parser')
    for i in crc_sections:
        if sections[i][1] != 1 or sections[i][3] != 0 or sections[i][5] % 4:
            raise ValueError('unsupported CRC section layout')
    exports = {}
    symbols_exported = set()
    covered = set()
    for section in sections:
        if section[1] != 2:  # SHT_SYMTAB
            continue
        if section[9] != 24 or section[5] % 24 or section[6] >= count:
            raise ValueError('invalid ELF64 symbol table')
        strings = contents(sections[section[6]])
        symbols = contents(section)
        for offset in range(0, len(symbols), 24):
            name_at, _, _, index, value, size = struct.unpack_from('<IBBHQQ', symbols, offset)
            name = string(strings, name_at)
            if name.startswith('__ksymtab_') and index not in (0, 0xfff1):
                symbols_exported.add(name[len('__ksymtab_'):])
            if not name.startswith('__crc_'):
                continue
            if index not in crc_sections or value % 4 or size not in (0, 4):
                raise ValueError('unsupported CRC symbol: ' + name)
            payload = contents(sections[index])
            if value + 4 > len(payload):
                raise ValueError('CRC symbol outside section')
            symbol = name[len('__crc_'):]
            if symbol in exports or (index, value) in covered:
                raise ValueError('duplicate CRC symbol or offset')
            exports[symbol] = struct.unpack_from('<I', payload, value)[0]
            covered.add((index, value))
    expected = {(i, at) for i in crc_sections for at in range(0, sections[i][5], 4)}
    if covered != expected or set(exports) != symbols_exported:
        raise ValueError('CRC table and named exports do not have exact coverage')
    return exports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ramdisk_lz4', type=Path)
    parser.add_argument('dlkm_root', type=Path, help='contains system_dlkm/ and vendor_dlkm/')
    parser.add_argument('vendor_ifas', type=Path)
    parser.add_argument('provider_reference', type=Path)
    parser.add_argument('live_exports', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists; choose a new report path')
    reference = json.loads(args.provider_reference.read_text())
    expected = {}
    for row in reference['modules']:
        if not row['path'].startswith('modules/'):
            raise ValueError('reference module path lacks modules/ prefix')
        path = row['path'][len('modules/'):]
        if path in expected:
            raise ValueError('duplicate reference path')
        expected[path] = row
    live = json.loads(args.live_exports.read_text())
    ramdisk = subprocess.check_output(['lz4', '-dc', str(args.ramdisk_lz4)])
    entries = [('vendor_boot/' + name, data) for name, data in cpio_entries(ramdisk)
               if name.endswith('.ko')]
    for directory in ('system_dlkm', 'vendor_dlkm'):
        for path in sorted((args.dlkm_root / directory).rglob('*.ko')):
            if not path.is_symlink():
                entries.append((path.relative_to(args.dlkm_root).as_posix(), path.read_bytes()))
    entries.append(('vendor/ifas.ko', args.vendor_ifas.read_bytes()))
    imports = defaultdict(list)
    providers = defaultdict(list)
    seen = set()
    exports_per_file = {}
    for path, data in entries:
        if path in seen or path not in expected:
            raise ValueError('unexpected or repeated module path: ' + path)
        seen.add(path)
        if hashlib.sha256(data).hexdigest() != expected[path]['sha256']:
            raise ValueError('hash mismatch: ' + path)
        info, required = module_metadata(data)
        name = info.get('name', [Path(path).stem.replace('-', '_')])[0]
        if name != expected[path]['name']:
            raise ValueError('module name mismatch: ' + path)
        exported = exported_crcs(data)
        exports_per_file[path] = len(exported)
        for symbol, crc in exported.items():
            providers[symbol].append({'path': path, 'module': name, 'crc': f'{crc:08x}'})
        for symbol, crc in required.items():
            if crc > 0xffffffff:
                raise ValueError('import CRC exceeds uint32')
            imports[symbol].append({'path': path, 'crc': f'{crc:08x}'})
    if seen != set(expected):
        raise ValueError('missing reference module files')
    comparisons = {}
    unresolved = []
    conflicts = {}
    for symbol, consumers in sorted(imports.items()):
        owners = live['exports'].get(symbol, [])
        if 'kernel' in owners:
            unresolved.append(symbol)
            continue
        candidates = [row for row in providers.get(symbol, []) if row['module'] in owners]
        if not candidates:
            unresolved.append(symbol)
            continue
        values = {row['crc'] for row in candidates + consumers}
        row = {'matches': len(values) == 1, 'providers': candidates,
               'import_crc_values': sorted({row['crc'] for row in consumers}),
               'consumer_files': len(consumers)}
        comparisons[symbol] = row
        if not row['matches']:
            conflicts[symbol] = row
    report = {
        'schema_version': 1, 'kernel_release': live['kernel'],
        'live_capture_utc': live['captured_utc'],
        'live_exports_sha256': hashlib.sha256(args.live_exports.read_bytes().replace(b'\r\n', b'\n')).hexdigest(),
        'reference_sha256': hashlib.sha256(args.provider_reference.read_bytes().replace(b'\r\n', b'\n')).hexdigest(),
        'module_files': len(seen), 'hashes_match_reference': True,
        'unique_module_export_names': len(providers),
        'unique_import_names': len(imports),
        'module_export_crc_comparisons': len(comparisons),
        'crc_conflicts': conflicts,
        'imports_without_checked_export_crc': unresolved,
        'exports_per_file': exports_per_file,
        'comparisons': comparisons,
        'limits': [
            'Base kernel export CRCs remain unchecked.',
            'Live export owner names select candidate files; they do not prove loaded bytes.',
            'All candidates for each observed owner must agree; partition duplicates are preserved.',
            'CRC equality does not validate namespaces, licenses, signatures, load ordering or complete ABI.',
            'This checks __versions and named __kcrctab exports, not all ELF undefined symbols.',
        ],
    }
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: report[k] for k in ('module_files', 'unique_module_export_names',
        'unique_import_names', 'module_export_crc_comparisons')}, indent=2))
    print('CRC conflicts:', len(conflicts))
    print('Imports without checked export CRC:', len(unresolved))
    if conflicts:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
