#!/usr/bin/env python3
"""Generate portable, metadata-only triage from an elf_deps schema 2 report.

This does not approve blobs for extraction or validate linker namespaces.
Usage: python3 tools/summarize_elf_audit.py ELF_REPORT OUTPUT_JSON
"""
import collections
import json
import sys
from pathlib import Path


def summarize(report):
    if report.get('schema_version') != 2:
        raise ValueError('requires elf_deps schema 2')
    inventory = report['elf_inventory']
    cross = {}
    for consumer, deps in report['candidate_providers'].items():
        if consumer.split('/')[0] not in ('vendor', 'odm'):
            continue
        for needed, providers in deps.items():
            external = [p for p in providers if p.split('/')[0] in ('system_ext','product')]
            local = [p for p in providers if p.split('/')[0] in ('vendor','odm')]
            if external:
                entry = cross.setdefault(needed, {'external_candidates':set(),
                    'vendor_odm_candidates':set(), 'consumers':set()})
                entry['external_candidates'].update(external)
                entry['vendor_odm_candidates'].update(local)
                entry['consumers'].add(consumer)
    absent = {}
    for consumer, names in report['unresolved'].items():
        for name in names:
            absent.setdefault(name, []).append(consumer)
    return {
        'schema_version':1,
        'scope':'vendor, odm, system_ext, product; installed rooted Android',
        'elf_files':len(inventory),
        'elf_by_partition':dict(sorted(collections.Counter(p.split('/')[0] for p in inventory).items())),
        'elf_by_machine':dict(sorted(collections.Counter(str(x['machine']) for x in inventory.values()).items())),
        'parse_or_read_errors':dict(sorted(report['parse_or_read_errors'].items())),
        'unsupported_elf':dict(sorted(report['unsupported_elf'].items())),
        'symlinks_not_followed_count':len(report['symlinks_not_followed']),
        'cross_partition_candidates':{name:{k:sorted(v) for k,v in entry.items()}
            for name,entry in sorted(cross.items())},
        'missing_provider_names':{name:sorted(consumers) for name,consumers in sorted(absent.items())},
        'platform_names_requiring_verification':report['platform_names_requiring_verification'],
        'additional_partition_elf':{p:v for p,v in sorted(inventory.items())
            if p.split('/')[0] in ('system_ext','product')},
        'limits':report['limits'] + [
            'Missing providers may belong to system/APEX, omitted aliases or unscanned formats.',
            'All additional partition entries require source-vs-blob review; none are approved packages.']}


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    report=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    result=summarize(report)
    Path(sys.argv[2]).write_bytes((json.dumps(result,indent=2,ensure_ascii=False)+'\n').encode())
    print('ELF files:',result['elf_files'])
    print('Cross-partition candidate names:',len(result['cross_partition_candidates']))
    print('Missing provider names:',len(result['missing_provider_names']))


if __name__ == '__main__':
    main()