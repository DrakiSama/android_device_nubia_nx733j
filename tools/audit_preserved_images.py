#!/usr/bin/env python3
"""Match four private stock B prebuilts to audited super extents and AVB parents.

Reads images without copying, mounting or modifying them. Output contains hashes
and descriptors, never private absolute paths or image bytes.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
from audit_dtbo_avb_envelope import vbmeta, require

NAMES = ('vendor', 'odm', 'vendor_dlkm', 'system_dlkm')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_at(stream, offset, size):
    stream.seek(offset)
    data = stream.read(size)
    require(len(data) == size, 'short image read')
    return data


def digest_region(stream, digest, offset, size):
    stream.seek(offset)
    while size:
        chunk = stream.read(min(size, 8 * 1024 * 1024))
        require(bool(chunk), 'truncated image region')
        digest.update(chunk)
        size -= len(chunk)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('avbtool', 'super_image', 'metadata', 'images_json', 'parent_vbmeta', 'output'):
        p.add_argument(name, type=Path)
    a = p.parse_args()
    require(not a.output.exists(), 'output exists; refuse overwrite')
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('avbtool', a.avbtool)
    avb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(avb)
    meta_bytes = a.metadata.read_bytes().replace(b'\r\n', b'\n')
    meta = json.loads(meta_bytes)
    require(not meta['discrepancies'], 'unresolved super discrepancies')
    selected = [m for m in meta['metadata'] if m['slot_index'] == 1 and not m['backup']]
    require(len(selected) == 1 and selected[0]['checksums_valid'], 'missing validated slot 1 map')
    selected = selected[0]
    parts = {p['name']: p for p in selected['partitions']}
    paths = json.loads(a.images_json.read_text(encoding='utf-8-sig'))
    require(set(paths) == set(NAMES), 'requires exactly the four preserved partition inputs')
    parent = a.parent_vbmeta.read_bytes()
    _, _, descriptors = vbmeta(avb, parent, 0, len(parent))
    results = {}
    with a.super_image.open('rb') as source:
        require(a.super_image.stat().st_size == meta['image_bytes'], 'super size differs')
        maximum = meta['geometry']['metadata_max_size']
        for backup in (False, True):
            record = next(m for m in meta['metadata'] if m['slot_index'] == 1 and m['backup'] == backup)
            offset = 12288 + maximum * (1 + (meta['geometry']['metadata_slots'] if backup else 0))
            raw = read_at(source, offset, maximum)
            header_size = struct.unpack_from('<I', raw, 8)[0]
            table_size = struct.unpack_from('<I', raw, 44)[0]
            require(header_size in (128, 256) and header_size + table_size <= maximum, 'metadata bounds')
            require(sha(raw[:header_size + table_size]) == record['sha256'] == selected['sha256'],
                    'actual super metadata differs from audited map')
        for name in NAMES:
            part = parts[name + '_b']
            image = Path(paths[name])
            require(image.stat().st_size == part['bytes'], 'image size differs: ' + name)
            digest = hashlib.sha256()
            total = 0
            for extent in part['extents']:
                require(extent['type'] == 0 and extent['source_index'] == 0, 'unsupported extent')
                start, size = extent['start_sector'] * 512, extent['sectors'] * 512
                require(0 <= start and start + size <= meta['image_bytes'], 'extent out of bounds')
                digest_region(source, digest, start, size)
                total += size
            require(total == part['bytes'], 'extent size sum differs')
            with image.open('rb') as stream:
                full = hashlib.sha256()
                digest_region(stream, full, 0, total)
                require(full.digest() == digest.digest(), 'image differs from super: ' + name)
                footer = avb.AvbFooter(read_at(stream, total - 64, 64))
                require(0 <= footer.original_image_size <= footer.vbmeta_offset
                        and footer.vbmeta_offset + footer.vbmeta_size <= total - 64, 'footer bounds')
                embedded = read_at(stream, footer.vbmeta_offset, footer.vbmeta_size)
            header, size, inner = vbmeta(avb, embedded, 0, len(embedded))
            require(size == footer.vbmeta_size, 'embedded metadata length differs')
            own = [d for d in inner if isinstance(d, avb.AvbHashtreeDescriptor) and d.partition_name == name]
            outer = [d for d in descriptors if isinstance(d, avb.AvbHashtreeDescriptor) and d.partition_name == name]
            require(len(own) == len(outer) == 1, 'missing or ambiguous hashtree descriptor')
            require(own[0].encode() == outer[0].encode(), 'parent and embedded descriptors differ')
            require(own[0].image_size == footer.original_image_size, 'hashtree data boundary differs')
            descriptor = {k: (v.hex() if isinstance(v, bytes) else v) for k, v in vars(own[0]).items()
                          if k not in ('tag', 'data')}
            results[name] = {'bytes': total, 'sha256': full.hexdigest(), 'matches_super_extents': True,
                             'footer_at_image_end': True, 'embedded_algorithm_type': header.algorithm_type,
                             'embedded_descriptor_matches_parent': True, 'descriptor': descriptor,
                             'descriptor_sha256': sha(own[0].encode())}
            print(name + ': image and AVB descriptor match', flush=True)
    report = {'schema_version': 1, 'created_utc': datetime.now(timezone.utc).isoformat(),
              'device': 'NX733J', 'reference_slot': 'b', 'profile': 'stock-b-build-only',
              'metadata_sha256_lf': sha(meta_bytes), 'avbtool_sha256': sha(a.avbtool.read_bytes()),
              'vbmeta_b_sha256': sha(parent), 'images': results,
              'limits': ['No image copy or build activation', 'No new signature verification',
                         'Hashtrees previously checked; this run matches exact images and descriptors',
                         'FEC recovery data not checked', 'Input map paths remain private']}
    with a.output.open('x', encoding='utf-8', newline='\n') as out:
        json.dump(report, out, indent=2)
        out.write('\n')


if __name__ == '__main__':
    main()
