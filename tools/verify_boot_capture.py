#!/usr/bin/env python3
"""Match local boot captures to audited bytes, without trusting AVB signatures."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

NAMES = ("boot", "init_boot", "vendor_boot", "dtbo", "vbmeta", "vbmeta_system")

def verify(directory, manifest):
    failures = []
    for name in NAMES:
        path = directory / (name + ".img")
        expected = manifest["images"][name]
        if not path.is_file():
            failures.append(name + ": missing image")
            continue
        if path.stat().st_size != expected["bytes"]:
            failures.append(name + ": size mismatch")
            continue
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            header = stream.read(4096)
            digest.update(header)
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected["sha256"]:
            failures.append(name + ": SHA-256 mismatch")
        if name in ("boot", "init_boot"):
            valid = len(header) >= 44 and header[:8] == b"ANDROID!"
            if valid:
                valid = struct.unpack_from("<I", header, 40)[0] == manifest[name]["header_version"]
                valid &= struct.unpack_from("<II", header, 8) == (manifest[name]["kernel_size"], manifest[name]["ramdisk_size"])
        elif name == "vendor_boot":
            valid = len(header) >= 2128 and header[:8] == b"VNDRBOOT"
            if valid:
                valid = struct.unpack_from("<II", header, 8) == (manifest[name]["header_version"], manifest[name]["page_size"])
                valid &= struct.unpack_from("<I", header, 2100)[0] == manifest[name]["dtb_size"]
        elif name == "dtbo":
            valid = len(header) >= 32 and struct.unpack_from(">I", header)[0] == 0xd7b7ab1e
            if valid:
                valid = struct.unpack_from(">I", header, 16)[0] == manifest[name]["entries"]
        else:
            valid = header[:4] == b"AVB0"
        if not valid:
            failures.append(name + ": header mismatch")
    return failures

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--manifest", type=Path, default=Path(__file__).resolve().parents[1] / "stock/boot-audit.json")
    args = parser.parse_args()
    try:
        failures = verify(args.directory, json.loads(args.manifest.read_text(encoding="utf-8")))
    except (OSError, KeyError, ValueError, struct.error, TypeError) as error:
        parser.exit(1, "Cannot verify capture: " + str(error) + "\n")
    if failures:
        parser.exit(1, "\n".join(failures) + "\n")
    print("All six images match audited sizes, SHA-256 and headers.")
    print("This matches the installed capture, NOT pristine firmware or verified AVB signatures.")
    print("Audited init_boot fails its parent vbmeta digest: do not use it as a clean prebuilt.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
