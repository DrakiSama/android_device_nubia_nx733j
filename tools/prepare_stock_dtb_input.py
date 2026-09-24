#!/usr/bin/env python3
"""Audit stock DTBO bounds and stage an intact DTB in a fresh private directory.

No DTBO output, AVB changes, build configuration, or device access.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference', type=Path)
    parser.add_argument('provider', type=Path)
    parser.add_argument('boot_audit', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; refuse overwrite or reuse')
    reference_bytes = args.reference.read_bytes().replace(b'\r\n', b'\n')
    reference = json.loads(reference_bytes)
    if reference['device'] != 'NX733J' or reference['provider_kind'] != 'stock_prebuilt':
        raise ValueError('requires NX733J stock provider reference')
    rows = {row['role']: row for row in reference['artifacts']}
    inputs = {}
    root = args.provider.resolve()
    for role in ('dtb', 'dtbo_reference'):
        row = rows[role]
        path = (root / row['path']).resolve()
        if root not in path.parents:
            raise ValueError('reference path escapes provider')
        data = path.read_bytes()
        if len(data) != row['bytes'] or digest(data) != row['sha256']:
            raise ValueError('stock reference mismatch: ' + role)
        inputs[role] = data
    data = inputs['dtbo_reference']
    magic, total, header, entry_size, count, offset, page, version = struct.unpack_from('>8I', data)
    if magic != 0xd7b7ab1e or version != 0 or header != 32 or entry_size != 32:
        raise ValueError('unsupported DTBO table format')
    table_end = offset + count * entry_size
    if not (header <= offset <= table_end <= total <= len(data)):
        raise ValueError('invalid DTBO table bounds')
    entries = []
    for index in range(count):
        size, start, ident, revision, *custom = struct.unpack_from('>8I', data, offset + index * entry_size)
        if size < 8 or start < table_end or start + size > total:
            raise ValueError('DTBO entry outside payload: ' + str(index))
        fdt_magic, fdt_size = struct.unpack_from('>2I', data, start)
        if fdt_magic != 0xd00dfeed or fdt_size != size:
            raise ValueError('DTBO entry FDT header mismatch: ' + str(index))
        entries.append({'index': index, 'offset': start, 'bytes': size,
                        'id': ident, 'revision': revision, 'custom': custom,
                        'sha256': digest(data[start:start + size])})
    audit_bytes = args.boot_audit.read_bytes().replace(b'\r\n', b'\n')
    audit = json.loads(audit_bytes)
    checks = [r for r in audit['avb']['descriptor_checks'] if r['partition'] == 'dtbo']
    if len(checks) != 1 or not checks[0]['matches_descriptor'] or checks[0]['hashed_bytes'] != total:
        raise ValueError('table size differs from previously verified stock descriptor')
    if audit['images']['dtbo']['sha256'] != digest(data):
        raise ValueError('boot audit references a different DTBO')
    tail = data[total:]
    report = {
        'schema_version': 1,
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'device': 'NX733J',
        'status': 'DTB_STAGED_DTBO_AUDITED_NOT_BUILD_INTEGRATED',
        'reference_sha256_lf': digest(reference_bytes),
        'boot_audit_sha256_lf': digest(audit_bytes),
        'dtb': {'output': 'dtb/nx733j-stock.dtb', 'bytes': len(inputs['dtb']),
                'sha256': digest(inputs['dtb']), 'transformation': 'filename only; entire payload'},
        'dtbo': {'partition_bytes': len(data), 'sha256': digest(data),
                 'table_total_bytes': total, 'entry_count': count, 'page_size': page,
                 'version': version, 'tail_bytes': len(tail),
                 'tail_nonzero_bytes': sum(value != 0 for value in tail),
                 'tail_sha256': digest(tail),
                 'avb_footer_magic_at_end': data[-64:-60] == b'AVBf',
                 'matches_previously_verified_descriptor_size': True,
                 'entries': entries},
        'limits': ['FDT header and bounds checked; overlay semantics not evaluated',
                   'AVB descriptor evidence reused from matching boot audit; no new signature check',
                   'No DTBO trimming, signing, build activation, or flashability claim']}
    args.output.mkdir(parents=True, exist_ok=False)
    target = args.output / report['dtb']['output']
    target.parent.mkdir()
    with target.open('xb') as stream:
        stream.write(inputs['dtb'])
    if digest(target.read_bytes()) != report['dtb']['sha256']:
        raise ValueError('DTB copy hash mismatch; partial output retained')
    with (args.output / 'preparation.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'status': report['status'], 'dtb_bytes': report['dtb']['bytes'],
                      'dtbo_entries': count, 'dtbo_tail_nonzero_bytes': report['dtbo']['tail_nonzero_bytes']}))


if __name__ == '__main__':
    main()
