#!/usr/bin/env python3
"""Regression checks for malformed input and false dependency satisfaction."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('elf_deps', Path(__file__).parents[1]/'elf_deps.py')
elf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(elf)

class ElfAuditTests(unittest.TestCase):
    def test_reference_dynamic_table(self):
        self.assertEqual(elf.parse_elf64(elf.build_synthetic_elf()), ('libself.so',['libfoo.so']))

    def test_dynamic_string_cannot_escape_strsz(self):
        data = bytearray(elf.build_synthetic_elf())
        struct.pack_into('<Q', data, 0x218, 13)
        with self.assertRaises(elf.ElfError):
            elf.parse_elf64(data)

    def test_out_of_range_needed(self):
        data = bytearray(elf.build_synthetic_elf())
        struct.pack_into('<Q', data, 0x228, 4096)
        with self.assertRaises(elf.ElfError):
            elf.parse_elf64(data)

    def test_truncated_program_headers(self):
        with self.assertRaises(elf.ElfError):
            elf.parse_elf64(elf.build_synthetic_elf()[:120])

    def test_unterminated_dynamic_table(self):
        data = bytearray(elf.build_synthetic_elf())
        struct.pack_into('<Q', data, 64+56+32, 64)
        with self.assertRaises(elf.ElfError):
            elf.parse_elf64(data)

    def test_architecture_and_platform_hints_do_not_satisfy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'consumer').write_bytes(elf.build_synthetic_elf())
            foreign = bytearray(elf.build_synthetic_elf())
            struct.pack_into('<H',foreign,18,62)
            (root/'libfoo.so').write_bytes(foreign)
            platform = elf.build_synthetic_elf().replace(b'libfoo.so',b'liblog.so')
            (root/'platform-consumer').write_bytes(platform)
            report = elf.dependency_report(root)
            self.assertEqual(report['unresolved']['consumer'],['libfoo.so'])
            self.assertEqual(report['unresolved']['platform-consumer'],['liblog.so'])
            self.assertIn('liblog.so',report['platform_names_requiring_verification'])

    def test_errors_and_unsupported_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'broken').write_bytes(b'\x7fELF')
            data = bytearray(elf.build_synthetic_elf())
            data[4]=1
            (root/'elf32').write_bytes(data)
            report = elf.dependency_report(root)
            self.assertIn('broken',report['parse_or_read_errors'])
            self.assertIn('elf32',report['unsupported_elf'])

    def test_symlink_outside_dump_is_not_parsed(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base/'root'
            root.mkdir()
            (base/'external').write_bytes(elf.build_synthetic_elf())
            try:
                (root/'external.so').symlink_to(base/'external')
            except OSError:
                self.skipTest('symlink creation unavailable')
            report = elf.dependency_report(root)
            self.assertEqual(report['elf_files'],0)
            self.assertIn('external.so',report['symlinks_not_followed'])

if __name__ == '__main__':
    unittest.main()