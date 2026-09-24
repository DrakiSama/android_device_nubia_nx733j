#!/usr/bin/env python3
"""Audit embedded DTBO AVB envelopes in stock partition captures, read-only.

Uses the selected avbtool parser but never its image mutation methods. No images
are extracted. Footer offsets are discovered from input bytes, not board guesses.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def vbmeta(avb, data, offset, bound):
    require(0 <= offset <= bound - 256 <= len(data) - 256, 'vbmeta header bounds')
    header = avb.AvbVBMetaHeader(data[offset:offset + 256])
    total = 256 + header.authentication_data_block_size + header.auxiliary_data_block_size
    require(offset + total <= bound, 'vbmeta blocks exceed bounds')
    require(header.descriptors_offset + header.descriptors_size <= header.auxiliary_data_block_size,
            'descriptor region outside auxiliary block')
    start = offset + 256 + header.authentication_data_block_size + header.descriptors_offset
    descriptors = avb.parse_descriptors(data[start:start + header.descriptors_size])
    return header, total, descriptors


def hash_fields(desc):
    return {name: getattr(desc, name) for name in ('partition_name', 'image_size', 'hash_algorithm', 'flags')} | {
        'salt': desc.salt.hex(), 'digest': desc.digest.hex()}


def inspect(avb, dtbo, parent):
    require(len(dtbo) >= 32, 'short DTBO')
    magic, total, header_size, entry_size, count, offset, page, version = struct.unpack_from('>8I', dtbo)
    require(magic == 0xd7b7ab1e and version == 0 and header_size == 32 and entry_size == 32,
            'unsupported DTBO header')
    table_end = offset + count * entry_size
    require(header_size <= offset <= table_end <= total <= len(dtbo), 'DTBO table bounds')
    for index in range(count):
        size, start = struct.unpack_from('>2I', dtbo, offset + index * entry_size)
        require(size >= 8 and table_end <= start and start + size <= total, 'DTBO entry bounds')
        require(struct.unpack_from('>2I', dtbo, start) == (0xd00dfeed, size), 'FDT entry size/magic')
    positions = []
    cursor = total
    while True:
        cursor = dtbo.find(b'AVBf', cursor)
        if cursor < 0:
            break
        positions.append(cursor)
        cursor += 4
    require(len(positions) == 1, 'expected one unambiguous footer candidate')
    footer_offset = positions[0]
    require(footer_offset + 64 <= len(dtbo), 'short footer candidate')
    footer = avb.AvbFooter(dtbo[footer_offset:footer_offset + 64])
    require(footer.version_major == 1 and footer.version_minor == 0, 'unsupported footer version')
    require(footer.original_image_size == total, 'footer original size differs from DTBO table')
    require(total <= footer.vbmeta_offset and footer.vbmeta_offset + footer.vbmeta_size <= footer_offset,
            'footer vbmeta bounds')
    embedded, size, descriptors = vbmeta(avb, dtbo, footer.vbmeta_offset, footer_offset)
    require(size == footer.vbmeta_size, 'footer vbmeta size differs from header')
    _, _, parent_descriptors = vbmeta(avb, parent, 0, len(parent))
    hashes = [x for x in descriptors if isinstance(x, avb.AvbHashDescriptor)]
    parent_hashes = [x for x in parent_descriptors if isinstance(x, avb.AvbHashDescriptor) and x.partition_name == 'dtbo']
    require(len(hashes) == 1 and len(parent_hashes) == 1, 'ambiguous DTBO descriptors')
    h = hashes[0]
    require(h.partition_name == 'dtbo' and h.image_size == total, 'embedded hash scope mismatch')
    require(hash_fields(h) == hash_fields(parent_hashes[0]), 'embedded and parent descriptors differ')
    computed = hashlib.new(h.hash_algorithm, h.salt + dtbo[:total]).hexdigest()
    require(computed == h.digest.hex(), 'DTBO payload hash mismatch')
    regions = [(total, footer.vbmeta_offset),
               (footer.vbmeta_offset + size, footer_offset),
               (footer_offset + 64, len(dtbo))]
    gaps = [{'start': a, 'end_exclusive': b, 'bytes': b - a,
             'nonzero_bytes': sum(x != 0 for x in dtbo[a:b]), 'sha256': sha(dtbo[a:b])} for a, b in regions]
    require(all(g['nonzero_bytes'] == 0 for g in gaps), 'unexplained nonzero bytes outside AVB envelope structures')
    require(embedded.algorithm_type == 0 and embedded.authentication_data_block_size == 0
            and embedded.signature_size == 0 and embedded.public_key_size == 0,
            'unexpected signed embedded vbmeta; requires separate signature audit')
    return {'partition_bytes': len(dtbo), 'partition_sha256': sha(dtbo),
            'parent_vbmeta_sha256': sha(parent), 'dtbo_table_bytes': total, 'dtbo_entries': count,
            'footer_offset': footer_offset, 'envelope_bytes': footer_offset + 64,
            'envelope_sha256': sha(dtbo[:footer_offset + 64]),
            'vbmeta_offset': footer.vbmeta_offset, 'vbmeta_bytes': size,
            'embedded_vbmeta_sha256': sha(dtbo[footer.vbmeta_offset:footer.vbmeta_offset + size]),
            'embedded_algorithm': 'NONE', 'embedded_rollback_index': embedded.rollback_index,
            'embedded_flags': embedded.flags, 'descriptor': hash_fields(h),
            'payload_matches_descriptor': True, 'descriptor_equals_parent': True,
            'all_other_trailing_regions_zero': True, 'gaps': gaps}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('avbtool', 'images', 'provider_dtbo', 'provider_reference', 'output'):
        p.add_argument(name, type=Path)
    args = p.parse_args()
    require(not args.output.exists(), 'output exists; refuse overwrite')
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('avbtool', args.avbtool)
    avb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(avb)
    ref_bytes = args.provider_reference.read_bytes().replace(b'\r\n', b'\n')
    ref = json.loads(ref_bytes)
    require(ref['device'] == 'NX733J' and ref['provider_kind'] == 'stock_prebuilt', 'wrong provider')
    provider = args.provider_dtbo.read_bytes()
    expected = [r for r in ref['artifacts'] if r['role'] == 'dtbo_reference']
    require(len(expected) == 1 and sha(provider) == expected[0]['sha256']
            and len(provider) == expected[0]['bytes'], 'provider DTBO differs from reference')
    slots = {}
    for slot in ('a', 'b'):
        data = (args.images / ('dtbo_' + slot + '.img')).read_bytes()
        parent = (args.images / ('vbmeta_' + slot + '.img')).read_bytes()
        slots[slot] = inspect(avb, data, parent)
    require(slots['b']['partition_sha256'] == sha(provider), 'backup B and provider differ')
    report = {'schema_version': 1, 'created_utc': datetime.now(timezone.utc).isoformat(),
              'device': 'NX733J', 'status': 'CONFIRMED_WITHIN_REPORTED_SCOPE',
              'avbtool_sha256': sha(args.avbtool.read_bytes()),
              'provider_reference_sha256_lf': sha(ref_bytes), 'provider_equals_backup_b': True,
              'slots': slots,
              'limits': ['Embedded vbmeta is unsigned (NONE); descriptor equality is not an embedded signature',
                         'Parent signatures were audited separately; this tool compares descriptors and payload hashes',
                         'Bootloader consumption of the internal footer is unknown',
                         'No key, rollback, OTA or restoration policy is selected',
                         'No image output or partition write']}
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'provider_equals_backup_b': True,
                      'slots': {k: {'envelope_bytes': v['envelope_bytes'],
                                    'hash_matches': v['payload_matches_descriptor'],
                                    'remaining_regions_zero': v['all_other_trailing_regions_zero']} for k, v in slots.items()}}))


if __name__ == '__main__':
    main()
