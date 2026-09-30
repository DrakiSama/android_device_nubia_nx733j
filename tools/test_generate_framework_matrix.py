#!/usr/bin/env python3
"""Pruebas de regresion de tools/generate_framework_matrix.py (sin red)."""

import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_framework_matrix as gfm  # noqa: E402

FRAGMENT_GNSS = """<manifest version="8.0" type="device">
    <hal format="aidl">
        <name>android.hardware.gnss</name>
        <version>4</version>
        <fqname>IGnss/default</fqname>
    </hal>
</manifest>
"""

FRAGMENT_DRM_A = """<manifest version="8.0" type="device">
    <hal format="aidl">
        <name>android.hardware.drm</name>
        <fqname>IDrmFactory/clearkey</fqname>
    </hal>
</manifest>
"""

FRAGMENT_DRM_B = """<manifest version="8.0" type="device">
    <hal format="aidl">
        <name>android.hardware.drm</name>
        <version>1</version>
        <fqname>IDrmFactory/wfdhdcp</fqname>
    </hal>
</manifest>
"""

ODM_MANIFEST = """<manifest version="8.0" type="device">
    <hal format="aidl">
        <name>vendor.zte.radio</name>
        <fqname>IVendorRadio/slot1</fqname>
        <fqname>IVendorRadio/slot2</fqname>
    </hal>
</manifest>
"""

NATIVE_FRAGMENT = """<manifest version="8.0" type="device">
    <hal format="native">
        <name>mapper</name>
        <fqname>@5.0/qti</fqname>
    </hal>
</manifest>
"""

INTERFACE_FORM_FRAGMENT = """<manifest version="1.0" type="device">
    <hal format="aidl">
        <name>vendor.qti.hardware.camera.offlinecamera</name>
        <version>1</version>
        <interface>
            <name>IOfflineCameraService</name>
            <instance>default</instance>
        </interface>
    </hal>
</manifest>
"""

COMPAT_MATRIX = """<compatibility-matrix version="8.0" type="device">
    <hal format="aidl" optional="true">
        <name>no.debe.entrar</name>
    </hal>
</compatibility-matrix>
"""

HIDL_FRAGMENT = """<manifest version="8.0" type="device">
    <hal format="hidl">
        <name>android.hardware.camera.provider</name>
        <transport>hwbinder</transport>
        <version>2.4</version>
        <interface>
            <name>ICameraProvider</name>
            <instance>legacy/0</instance>
        </interface>
    </hal>
</manifest>
"""


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


class GenerateFrameworkMatrixTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.vendor = self.root / "vendor/etc/vintf"
        self.odm = self.root / "odm/etc/vintf"
        write(self.vendor / "manifest/a.xml", FRAGMENT_GNSS)
        write(self.vendor / "manifest/b.xml", FRAGMENT_DRM_A)
        write(self.vendor / "manifest/c.xml", FRAGMENT_DRM_B)
        write(self.vendor / "manifest/mapper.qti.xml", NATIVE_FRAGMENT)
        write(self.vendor / "manifest/d.xml", INTERFACE_FORM_FRAGMENT)
        write(self.vendor / "compatibility_matrix.xml", COMPAT_MATRIX)
        write(self.odm / "manifest.xml", ODM_MANIFEST)
        self.out = self.root / "out/fcm.xml"

    def tearDown(self):
        self.tmp.cleanup()

    def run_tool(self):
        rc = gfm.main([
            "--manifest-dir", str(self.vendor),
            "--manifest-dir", str(self.odm),
            "-o", str(self.out),
        ])
        self.assertEqual(rc, 0)
        return ET.parse(str(self.out)).getroot()

    def test_genera_hal_por_nombre_y_version(self):
        root = self.run_tool()
        self.assertEqual(root.tag, "compatibility-matrix")
        self.assertEqual(root.get("type"), "framework")
        hals = root.findall("hal")
        entries = [(h.get("format"), h.findtext("name"),
                    tuple(v.text for v in h.findall("version")))
                   for h in hals]
        self.assertEqual(entries, [
            ("aidl", "android.hardware.drm", ()),
            ("aidl", "android.hardware.drm", ("1",)),
            ("aidl", "android.hardware.gnss", ("4",)),
            ("aidl", "vendor.qti.hardware.camera.offlinecamera", ("1",)),
            ("aidl", "vendor.zte.radio", ()),
            ("native", "mapper", ("5.0",)),
        ])
        for hal in hals:
            self.assertEqual(hal.get("optional"), "true")

    def test_interface_form(self):
        root = self.run_tool()
        camera = [h for h in root.findall("hal")
                  if h.findtext("name") ==
                  "vendor.qti.hardware.camera.offlinecamera"][0]
        iface = camera.find("interface")
        self.assertEqual(iface.findtext("name"), "IOfflineCameraService")
        self.assertEqual(iface.findtext("instance"), "default")

    def test_native_mapper(self):
        root = self.run_tool()
        mapper = [h for h in root.findall("hal")
                  if h.findtext("name") == "mapper"][0]
        self.assertEqual(mapper.get("format"), "native")
        self.assertEqual(mapper.findtext("version"), "5.0")
        iface = mapper.find("interface")
        self.assertIsNone(iface.find("name"))
        self.assertEqual(iface.findtext("instance"), "qti")

    def test_dedup_e_interfaces(self):
        root = self.run_tool()
        radio = [h for h in root.findall("hal")
                 if h.findtext("name") == "vendor.zte.radio"][0]
        self.assertEqual(len(radio.findall("interface")), 1)
        radio_iface = radio.find("interface")
        self.assertEqual(radio_iface.findtext("name"), "IVendorRadio")
        instances = [i.text for i in radio_iface.findall("instance")]
        self.assertEqual(instances, ["slot1", "slot2"])
        gnss = [h for h in root.findall("hal")
                if h.findtext("name") == "android.hardware.gnss"][0]
        iface = gnss.find("interface")
        self.assertEqual(iface.findtext("name"), "IGnss")
        self.assertEqual(iface.findtext("instance"), "default")

    def test_ignora_archivos_de_matriz(self):
        root = self.run_tool()
        names = [h.findtext("name") for h in root.findall("hal")]
        self.assertNotIn("no.debe.entrar", names)

    def test_deterministico(self):
        self.run_tool()
        first = self.out.read_bytes()
        self.run_tool()
        self.assertEqual(first, self.out.read_bytes())

    def test_rechaza_hidl(self):
        write(self.vendor / "manifest/hidl.xml", HIDL_FRAGMENT)
        with self.assertRaises(SystemExit):
            gfm.main([
                "--manifest-dir", str(self.vendor),
                "-o", str(self.out),
            ])


if __name__ == "__main__":
    unittest.main()
