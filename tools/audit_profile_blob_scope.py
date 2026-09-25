#!/usr/bin/env python3
"""Audit inventory partition scope against a build profile; never approve extraction.

Accepts plain relative-path inventories only. Extract-utils remaps/flags are
rejected rather than misclassified. No image or device access is performed.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('profile', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('inventories', nargs='+', type=Path)
    a = p.parse_args()
    if a.output.exists():
        p.error('output exists; refusing overwrite')
    raw = a.profile.read_bytes()
    profile = json.loads(raw)
    specs = profile['partitions']
    reports = []
    for inventory in a.inventories:
        data = inventory.read_bytes()
        counts, decisions, seen = Counter(), Counter(), set()
        for number, line in enumerate(data.decode('utf-8-sig').splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            path = PurePosixPath(line)
            if (path.is_absolute() or '..' in path.parts or len(path.parts) < 2
                    or any(c in line for c in ':;|\\') or line.startswith('-')
                    or any(c.isspace() for c in line) or str(path) != line):
                p.error(f'{inventory.name}:{number}: expected plain relative inventory path')
            if line in seen:
                p.error(f'{inventory.name}:{number}: duplicate path')
            seen.add(line)
            partition = path.parts[0]
            counts[partition] += 1
            action = specs.get(partition, {}).get('action', 'unknown')
            if action == 'preserve_stock_b_prebuilt':
                decisions['already_inside_preserved_image_do_not_extract_individually'] += 1
            elif action == 'rebuild':
                decisions['review_source_or_blob_no_install_approval'] += 1
            else:
                decisions['unknown_profile_scope'] += 1
        reports.append({'inventory': inventory.name, 'sha256': hashlib.sha256(data).hexdigest(),
                        'entries': len(seen), 'partitions': dict(sorted(counts.items())),
                        'scope': dict(sorted(decisions.items()))})
    report = {'schema_version': 1, 'profile_sha256': hashlib.sha256(raw).hexdigest(),
              'inventories': reports, 'extraction_approved': False,
              'limitations': ['Partition scope only, not dependency closure or necessity.',
                             'No namespace, ABI, SELinux, VINTF or license decisions.',
                             'Whole-image preservation does not prove framework compatibility.']}
    with a.output.open('x', encoding='utf-8') as f:
        f.write(json.dumps(report, indent=2) + '\n')
    print(json.dumps(reports, indent=2))


if __name__ == '__main__':
    main()
