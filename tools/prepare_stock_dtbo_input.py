#!/usr/bin/env python3
"""Stage the audited stock DTBO AVB envelope in a new private directory.

Preserves every byte through the existing footer. Omits only the verified zero
suffix of the full partition capture. Does not sign or build a ROM image.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('audit', 'provider_dtbo', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; refuse overwrite or reuse')
    audit_bytes = args.audit.read_bytes().replace(b'\r\n', b'\n')
    audit = json.loads(audit_bytes)
    if audit['device'] != 'NX733J' or not audit['provider_equals_backup_b']:
        raise ValueError('requires audited NX733J backup/provider equality')
    ref = audit['slots']['b']
    data = args.provider_dtbo.read_bytes()
    if len(data) != ref['partition_bytes'] or sha(data) != ref['partition_sha256']:
        raise ValueError('input differs from audited stock B')
    end = ref['envelope_bytes']
    if not (64 <= end < len(data)) or ref['footer_offset'] != end - 64:
        raise ValueError('invalid envelope bound')
    magic, major, minor, original, vbmeta_offset, vbmeta_size = struct.unpack_from('>4sIIQQQ', data, end - 64)
    if (magic, major, minor, original, vbmeta_offset, vbmeta_size) != (
            b'AVBf', 1, 0, ref['dtbo_table_bytes'], ref['vbmeta_offset'], ref['vbmeta_bytes']):
        raise ValueError('footer differs from audit')
    if not ref['all_other_trailing_regions_zero'] or any(data[end:]):
        raise ValueError('suffix is not audited zero padding')
    payload = data[:end]
    if sha(payload) != ref['envelope_sha256']:
        raise ValueError('envelope hash differs from audit')
    args.output.mkdir(parents=True, exist_ok=False)
    target = args.output / 'dtbo.img'
    with target.open('xb') as stream:
        stream.write(payload)
    if sha(target.read_bytes()) != ref['envelope_sha256']:
        raise ValueError('output copy hash mismatch; partial directory retained')
    report = {'schema_version': 1, 'created_utc': datetime.now(timezone.utc).isoformat(),
              'device': 'NX733J', 'status': 'STOCK_ENVELOPE_STAGED_NOT_ROM_IMAGE',
              'audit_sha256_lf': sha(audit_bytes), 'source_bytes': len(data),
              'source_sha256': sha(data), 'output': 'dtbo.img', 'output_bytes': len(payload),
              'output_sha256': sha(payload), 'omitted_zero_suffix_bytes': len(data) - end,
              'partition_size_unchanged': len(data), 'existing_avb_footer_preserved': True,
              'existing_embedded_algorithm': ref['embedded_algorithm'],
              'limits': ['Work input only; no new signature or AVB policy',
                         'No build, OTA or flash operation',
                         'Full partition reference remains unchanged']}
    with (args.output / 'preparation.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'status': report['status'], 'output_bytes': len(payload),
                      'omitted_zero_suffix_bytes': len(data) - end}))


if __name__ == '__main__':
    main()
