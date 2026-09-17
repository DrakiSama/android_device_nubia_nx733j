#!/usr/bin/env python3
"""Parse DT_NEEDED/DT_SONAME of ELF64 files and check dependency coverage.

Pure Python, no third-party packages. Works on any directory of extracted
files (a future vendor/odm dump) and reports needed libraries that are not
provided by the blob list nor by the AOSP/LineageOS core allowlist.

Usage:
  python3 tools/elf_deps.py --selftest
  python3 tools/elf_deps.py /path/to/dump/root [--report out.json]
"""
import json
import struct
import sys
from pathlib import Path

PT_DYNAMIC = 2
DT_NEEDED = 1
DT_STRTAB = 5
DT_STRSZ = 10
DT_SONAME = 14
DT_NULL = 0

# Libraries that AOSP/LineageOS builds from source and are never vendor blobs.
# Extend deliberately when a missing-dependency report proves one is core.
AOSP_CORE_LIBS = {
    'ld-android.so', 'libandroid.so', 'libbase.so', 'libbinder.so',
    'libbinder_ndk.so', 'libc.so', 'libcap.so', 'libcutils.so', 'libdl.so',
    'libdl_android.so', 'libexpat.so', 'libhardware.so', 'libhidlbase.so',
    'liblog.so', 'libm.so', 'libmediandk.so', 'libminijail.so',
    'libnetd_client.so', 'libpcre2.so', 'libprocessgroup.so',
    'libprotobuf-cpp-lite.so', 'libselinux.so', 'libssl.so', 'libcrypto.so',
    'libui.so', 'libutils.so', 'libvndksupport.so', 'libz.so',
}


class ElfError(Exception):
    pass


def parse_elf64(data):
    """Return (soname|None, [needed...]) for an ELF64 LE shared object/binary."""
    if len(data) < 64 or data[:4] != b'\x7fELF':
        raise ElfError('not an ELF file')
    if data[4] != 2 or data[5] != 1:
        raise ElfError('only ELF64 little-endian is supported')
    e_phoff = struct.unpack_from('<Q', data, 32)[0]
    e_phentsize = struct.unpack_from('<H', data, 54)[0]
    e_phnum = struct.unpack_from('<H', data, 56)[0]
    dyn_off = None
    dyn_size = 0
    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        if off + 56 > len(data):
            raise ElfError('truncated program header')
        p_type = struct.unpack_from('<I', data, off)[0]
        if p_type == PT_DYNAMIC:
            dyn_off = struct.unpack_from('<Q', data, off + 8)[0]
            dyn_size = struct.unpack_from('<Q', data, off + 32)[0]
            break
    if dyn_off is None:
        return None, []
    strtab_addr = strsz = None
    soname = None
    needed_raw = []
    entries = dyn_size // 16
    for i in range(entries):
        off = dyn_off + i * 16
        if off + 16 > len(data):
            raise ElfError('truncated dynamic section')
        tag, val = struct.unpack_from('<qQ', data, off)
        if tag == DT_NULL:
            break
        if tag == DT_STRTAB:
            strtab_addr = val
        elif tag == DT_STRSZ:
            strsz = val
        elif tag == DT_NEEDED:
            needed_raw.append(val)
        elif tag == DT_SONAME:
            soname = val
    if strtab_addr is None or strsz is None:
        raise ElfError('dynamic section without string table')
    # In files, the string table virtual address usually equals its file offset
    # for the first LOAD segment; find the mapping via program headers instead.
    strtab_off = vaddr_to_offset(data, strtab_addr, e_phoff, e_phentsize, e_phnum)
    if strtab_off is None or strtab_off + strsz > len(data):
        raise ElfError('string table out of range')

    def read_str(at):
        end = data.index(b'\x00', strtab_off + at)
        return data[strtab_off + at:end].decode('utf-8', 'replace')

    needed = [read_str(n) for n in needed_raw]
    return (read_str(soname) if soname is not None else None), needed


def vaddr_to_offset(data, vaddr, e_phoff, e_phentsize, e_phnum):
    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        p_type = struct.unpack_from('<I', data, off)[0]
        if p_type != 1:  # PT_LOAD
            continue
        p_offset, p_vaddr, _, p_filesz = struct.unpack_from('<QQQQ', data, off + 8)
        if p_vaddr <= vaddr < p_vaddr + p_filesz:
            return p_offset + (vaddr - p_vaddr)
    return None


def scan_root(root):
    """Return {relpath: {'soname':..., 'needed':[...]}} for all ELF64 files."""
    found = {}
    for path in sorted(root.rglob('*')):
        try:
            if not path.is_file():
                continue
            data = path.read_bytes()
        except OSError:
            # Cloud placeholders, reparse points and unreadable files are skipped.
            continue
        try:
            soname, needed = parse_elf64(data)
        except ElfError:
            continue
        found[str(path.relative_to(root))] = {'soname': soname, 'needed': needed}
    return found


def build_synthetic_elf():
    """Minimal ELF64 LE with one LOAD, one DYNAMIC and a string table."""
    strtab = b'\x00libself.so\x00libfoo.so\x00'
    phoff = 64
    dyn_off = 0x200
    strtab_off = 0x300
    header = bytearray(64)
    header[:4] = b'\x7fELF'
    header[4] = 2  # 64-bit
    header[5] = 1  # little-endian
    header[6] = 1  # version
    struct.pack_into('<H', header, 16, 3)  # ET_DYN
    struct.pack_into('<H', header, 18, 0xB7)  # AArch64
    struct.pack_into('<I', header, 20, 1)
    struct.pack_into('<Q', header, 32, phoff)
    struct.pack_into('<H', header, 54, 56)
    struct.pack_into('<H', header, 56, 2)
    ph = bytearray(112)
    struct.pack_into('<I', ph, 0, 1)  # PT_LOAD
    struct.pack_into('<QQQQ', ph, 8, 0, 0, 0, 0x400)  # offset,vaddr,paddr,filesz
    struct.pack_into('<Q', ph, 32, 0x400)  # memsz
    struct.pack_into('<I', ph, 56, PT_DYNAMIC)
    struct.pack_into('<QQQQ', ph, 64, dyn_off, dyn_off, dyn_off, 4 * 16)
    struct.pack_into('<Q', ph, 88, 4 * 16)
    dyn = bytearray(64)
    struct.pack_into('<qQ', dyn, 0, DT_STRTAB, strtab_off)
    struct.pack_into('<qQ', dyn, 16, DT_STRSZ, len(strtab))
    struct.pack_into('<qQ', dyn, 32, DT_NEEDED, 12)  # 'libfoo.so'
    struct.pack_into('<qQ', dyn, 48, DT_SONAME, 1)  # 'libself.so'
    blob = bytearray(0x400)
    blob[:64] = header
    blob[phoff:phoff + 112] = ph
    blob[dyn_off:dyn_off + 64] = dyn
    blob[strtab_off:strtab_off + len(strtab)] = strtab
    return bytes(blob)


def selftest():
    soname, needed = parse_elf64(build_synthetic_elf())
    assert soname == 'libself.so', soname
    assert needed == ['libfoo.so'], needed
    try:
        parse_elf64(b'not an elf')
        raise SystemExit('selftest: non-ELF input was not rejected')
    except ElfError:
        pass
    print('elf_deps selftest OK: soname and DT_NEEDED parsed; non-ELF rejected')
    return 0


def main():
    args = sys.argv[1:]
    if args and args[0] == '--selftest':
        return selftest()
    if not args:
        print(__doc__)
        return 2
    root = Path(args[0]).resolve()
    report_path = None
    if '--report' in args:
        report_path = Path(args[args.index('--report') + 1])
    if not root.is_dir():
        print(f'not a directory: {root}', file=sys.stderr)
        return 2

    scanned = scan_root(root)
    providers = set(AOSP_CORE_LIBS)
    for info in scanned.values():
        if info['soname']:
            providers.add(info['soname'])
    for rel in scanned:
        providers.add(Path(rel).name)

    unresolved = {}
    for rel, info in scanned.items():
        missing = [n for n in info['needed'] if n not in providers]
        if missing:
            unresolved[rel] = missing

    summary = {
        'root': str(root),
        'elf_files': len(scanned),
        'files_with_unresolved_deps': len(unresolved),
        'unresolved': unresolved,
    }
    text = json.dumps(summary, indent=2, ensure_ascii=False) + '\n'
    if report_path:
        report_path.write_bytes(text.encode('utf-8'))
    print(f'elf_files={len(scanned)} files_with_unresolved_deps={len(unresolved)}')
    for rel in sorted(unresolved):
        print(f'  {rel}: {", ".join(unresolved[rel])}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
