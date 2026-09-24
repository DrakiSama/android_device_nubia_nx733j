#!/usr/bin/env python3
"""Audit NX733J pvmfw A/B headers, GPT sizes and parent AVB hashes, read-only."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
from audit_dtbo_avb_envelope import vbmeta, hash_fields, require


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('avbtool', 'images', 'gpt_audit', 'output'):
        p.add_argument(name, type=Path)
    args = p.parse_args()
    require(not args.output.exists(), 'output exists; refuse overwrite')
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('avbtool', args.avbtool)
    avb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(avb)
    gpt_bytes = args.gpt_audit.read_bytes().replace(b'\r\n', b'\n')
    gpt = json.loads(gpt_bytes)
    slots = {}
    for slot in ('a', 'b'):
        name = 'pvmfw_' + slot
        partitions = []
        for lun in gpt['luns']:
            for header in lun['headers']:
                for part in header['partitions']:
                    if part['label'] == name:
                        partitions.append((lun['lun'], part['bytes'], part['start_sector'], part['end_sector']))
        require(partitions and len(set(partitions)) == 1, 'GPT pvmfw copies missing or differ')
        data = (args.images / (name + '.img')).read_bytes()
        parent = (args.images / ('vbmeta_system_' + slot + '.img')).read_bytes()
        require(len(data) == partitions[0][1], 'pvmfw size differs from GPT')
        require(data[:8] == b'ANDROID!' and len(data) >= 4096, 'unknown pvmfw container')
        version = struct.unpack_from('<I', data, 40)[0]
        require(version in (3, 4), 'pvmfw boot header needs separate audit')
        kernel_size, ramdisk_size, os_version, header_size = struct.unpack_from('<4I', data, 8)
        require(header_size == (1584 if version == 4 else 1580), 'boot header size mismatch')
        signature_size = struct.unpack_from('<I', data, 1580)[0] if version == 4 else 0
        aligned = lambda x: (x + 4095) & ~4095
        used = 4096 + aligned(kernel_size) + aligned(ramdisk_size) + aligned(signature_size)
        require(used <= len(data), 'pvmfw payload bounds')
        _, _, descriptors = vbmeta(avb, parent, 0, len(parent))
        hashes = [x for x in descriptors if isinstance(x, avb.AvbHashDescriptor) and x.partition_name == 'pvmfw']
        require(len(hashes) == 1, 'pvmfw parent descriptor missing or ambiguous')
        desc = hashes[0]
        require(desc.image_size == used, 'hashed prefix differs from computed payload extent')
        require(hashlib.new(desc.hash_algorithm, desc.salt + data[:used]).hexdigest() == desc.digest.hex(),
                'pvmfw hash differs from parent')
        footer_present = data[-64:-60] == b'AVBf'
        footer_data = None
        if footer_present:
            footer = avb.AvbFooter(data[-64:])
            require(footer.original_image_size == used, 'footer original size mismatch')
            require(used <= footer.vbmeta_offset and footer.vbmeta_offset + footer.vbmeta_size <= len(data) - 64,
                    'footer metadata bounds')
            h, size, embedded = vbmeta(avb, data, footer.vbmeta_offset, len(data) - 64)
            require(size == footer.vbmeta_size, 'embedded vbmeta size mismatch')
            ih = [x for x in embedded if isinstance(x, avb.AvbHashDescriptor) and x.partition_name == 'pvmfw']
            require(len(ih) == 1 and hash_fields(ih[0]) == hash_fields(desc), 'embedded hash differs from parent')
            footer_data = {'vbmeta_offset': footer.vbmeta_offset, 'vbmeta_bytes': size,
                           'algorithm_type': h.algorithm_type, 'descriptor_equals_parent': True}
        slots[slot] = {'partition': name, 'lun': partitions[0][0], 'partition_bytes': len(data),
                       'partition_sha256': sha(data), 'parent_vbmeta_system_sha256': sha(parent),
                       'boot_header_version': version, 'header_bytes': header_size,
                       'kernel_field_bytes': kernel_size, 'ramdisk_field_bytes': ramdisk_size,
                       'os_version_field': os_version, 'boot_signature_bytes': signature_size,
                       'payload_extent_bytes': used, 'descriptor': hash_fields(desc),
                       'payload_matches_parent_descriptor': True, 'footer_at_partition_end': footer_present,
                       'footer': footer_data}
    report = {'schema_version': 1, 'captured_utc': datetime.now(timezone.utc).isoformat(),
              'device': 'NX733J', 'source': '9008 backup images; GPT audit and vbmeta_system per slot',
              'gpt_audit_sha256_lf': sha(gpt_bytes), 'avbtool_sha256': sha(args.avbtool.read_bytes()),
              'slots': slots, 'slot_images_identical': slots['a']['partition_sha256'] == slots['b']['partition_sha256'],
              'limits': ['Boot-container kernel field is a format name, not the Android kernel provider',
                         'Hashes and containers checked; firmware execution and bootloader acceptance not tested',
                         'Parent signatures audited separately', 'No pvmfw image generation, OTA policy or flashing']}
    with args.output.open('x', encoding='utf-8', newline='\n') as out:
        json.dump(report, out, indent=2)
        out.write('\n')
    print(json.dumps({slot: {'header_version': r['boot_header_version'], 'hashed_bytes': r['payload_extent_bytes'],
                            'footer': r['footer']} for slot, r in slots.items()}))


if __name__ == '__main__':
    main()
