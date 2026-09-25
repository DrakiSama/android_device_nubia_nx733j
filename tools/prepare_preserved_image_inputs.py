#!/usr/bin/env python3
"""Stage Linux symlinks and a dormant Make fragment for verified stock images.

Reads images; never changes their contents. Output is private and not auto-included.
This checks full-file identity only, not AVB signatures, FEC or ROM compatibility.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re

VARIABLES = {
    'vendor': 'BOARD_PREBUILT_VENDORIMAGE',
    'odm': 'BOARD_PREBUILT_ODMIMAGE',
    'vendor_dlkm': 'BOARD_PREBUILT_VENDOR_DLKMIMAGE',
    'system_dlkm': 'BOARD_PREBUILT_SYSTEM_DLKMIMAGE',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profile', type=Path)
    parser.add_argument('inputs', type=Path, help='private JSON mapping partition to Linux image path')
    parser.add_argument('destination', type=Path, help='new private absolute Linux directory, no spaces')
    args = parser.parse_args()
    if os.name != 'posix':
        parser.error('run inside the Linux build environment')
    dest = args.destination
    if not dest.is_absolute() or not re.fullmatch(r'/[A-Za-z0-9_./-]+', str(dest)):
        parser.error('destination must be an absolute Make-safe path')
    # Check lexical path before resolve: a dangling symlink also counts as existing.
    if os.path.lexists(dest):
        parser.error('destination exists; refusing overwrite')
    dest = dest.resolve()
    if not re.fullmatch(r'/[A-Za-z0-9_./-]+', str(dest)):
        parser.error('resolved destination is not Make-safe')
    profile_bytes = args.profile.read_bytes()
    profile = json.loads(profile_bytes)
    if (profile.get('device') != 'NX733J' or profile.get('reference_firmware_slot') != 'b'
            or profile.get('status') != 'DESIGN_NOT_ACTIVATED'
            or profile.get('flash_ready') is not False):
        parser.error('expected inactive NX733J stock B profile')
    inputs = json.loads(args.inputs.read_text())
    if set(inputs) != set(VARIABLES):
        parser.error('input map must contain exactly vendor, odm, vendor_dlkm, system_dlkm')
    verified = {}
    for part in VARIABLES:
        spec = profile['partitions'][part]
        if spec['action'] != 'preserve_stock_b_prebuilt':
            parser.error('unexpected producer for ' + part)
        path = Path(inputs[part]).resolve(strict=True)
        if not path.is_file() or path.stat().st_size != spec['bytes']:
            parser.error('size/type mismatch for ' + part)
        digest = hashlib.sha256()
        with path.open('rb') as image:
            for chunk in iter(lambda: image.read(8 * 1024 * 1024), b''):
                digest.update(chunk)
        if digest.hexdigest() != spec['sha256']:
            parser.error('SHA-256 mismatch for ' + part)
        verified[part] = {'source': str(path), 'bytes': spec['bytes'], 'sha256': digest.hexdigest()}
    # No outputs until all inputs pass. Partial outputs on I/O failure are retained;
    # rerun with a new directory after inspection, never overwrite existing evidence.
    dest.mkdir(parents=False, exist_ok=False)
    lines = ['# PRIVATE: verified source identities, not build/flash approval.',
             '# Not included automatically. Resolve AVB/vendor product integration first.',
             '# Symlinks are not immutable: recheck source identities before each build.']
    for part, variable in VARIABLES.items():
        target = dest / (part + '.img')
        target.symlink_to(verified[part]['source'])
        lines.append(variable + ' := ' + str(target))
    (dest / 'BoardConfigPreservedImages.mk').write_text('\n'.join(lines) + '\n')
    report = {'schema_version': 1, 'status': 'PREPARED_NOT_ACTIVATED',
              'profile_sha256': hashlib.sha256(profile_bytes).hexdigest(),
              'images': verified, 'flash_ready': False}
    (dest / 'manifest.private.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'verified_images': len(verified),
                      'bytes_hashed': sum(x['bytes'] for x in verified.values())}))


if __name__ == '__main__':
    main()
