#!/usr/bin/env python3
"""Genera las adiciones del dispositivo a la matriz de compatibilidad del
framework (FCM) del NX733J a partir de los manifiestos VINTF capturados del
vendor/ODM stock.

Entradas: directorios que contengan manifiestos VINTF (fragmentos en
``manifest/*.xml`` y/o archivos ``*.xml`` con raiz ``<manifest>``). Los
archivos de matriz (``compatibility_matrix*.xml``) se ignoran.

Salida: un ``<compatibility-matrix type="framework">`` con una entrada
``<hal optional="true">`` por (formato, nombre, versiones) observado, con sus
interfaces e instancias (aidl) o instancias (native). Deterministico: mismo
input, mismo output.

Uso:
    python3 tools/generate_framework_matrix.py \\
        --manifest-dir <ruta>/vendor/etc/vintf \\
        --manifest-dir <ruta>/odm/etc/vintf \\
        -o vintf/framework_compatibility_matrix.xml
"""

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MATRIX_VERSION = "9.0"
PROVENANCE = (
    "Generado por tools/generate_framework_matrix.py desde los manifiestos "
    "VINTF stock del dispositivo; no editar a mano."
)


def manifest_files(root):
    """Archivos candidatos a manifiesto dentro de un directorio etc/vintf."""
    files = [f for f in sorted(root.glob("*.xml"))]
    mdir = root / "manifest"
    if mdir.is_dir():
        files.extend(sorted(mdir.glob("*.xml")))
    return files


def parse_manifest(path):
    """Devuelve las entradas <hal> de un manifiesto, o None si no lo es.

    Cada entrada: (format, name, versions, interfaces) donde interfaces es una
    lista de (interface, instance); para format="native" la interface es None
    y la version/instancia vienen del fqname "@VERSION/instancia".
    """
    try:
        root = ET.parse(str(path)).getroot()
    except ET.ParseError as exc:
        raise SystemExit("XML invalido en %s: %s" % (path, exc))
    if root.tag != "manifest":
        return None
    hals = []
    for hal in root.findall("hal"):
        fmt = hal.get("format", "hidl")
        name = hal.findtext("name")
        if not name:
            raise SystemExit("HAL sin <name> en %s" % path)
        if fmt not in ("aidl", "native"):
            raise SystemExit(
                "HAL %s con format=%s en %s: solo se esperan aidl/native; "
                "revisar el generador." % (name, fmt, path)
            )
        versions = tuple(v.text for v in hal.findall("version"))
        fqnames = [fq.text or "" for fq in hal.findall("fqname")]
        interfaces = []
        if fmt == "aidl":
            for fq in fqnames:
                iface, sep, instance = fq.partition("/")
                if not sep:
                    raise SystemExit("fqname invalido %r en %s" % (fq, path))
                interfaces.append((iface, instance))
            for itf in hal.findall("interface"):
                iname = itf.findtext("name")
                iinst = itf.findtext("instance")
                if not iname or not iinst:
                    raise SystemExit(
                        "<interface> incompleta en %s (hal %s)" % (path, name))
                interfaces.append((iname, iinst))
        else:
            # native: fqname "@VERSION/instance" aporta version e instancia.
            for fq in fqnames:
                if not fq.startswith("@") or "/" not in fq:
                    raise SystemExit("fqname native invalido %r en %s" % (fq, path))
                ver, _, instance = fq[1:].partition("/")
                versions = versions + (ver,)
                interfaces.append((None, instance))
            if hal.findall("interface"):
                raise SystemExit(
                    "<interface> en hal native %s (%s): no esperado" % (name, path))
        if not interfaces:
            raise SystemExit("HAL %s sin fqnames/interface en %s" % (name, path))
        hals.append((fmt, name, versions, interfaces))
    return hals


def collect(manifest_dirs):
    """Agrupa por (format, nombre, versiones) y une interfaces/instancias."""
    entries = {}
    files = 0
    for d in manifest_dirs:
        root = Path(d)
        if not root.is_dir():
            raise SystemExit("No es un directorio: %s" % d)
        for path in manifest_files(root):
            hals = parse_manifest(path)
            if hals is None:
                continue
            files += 1
            for fmt, name, versions, interfaces in hals:
                key = (fmt, name, versions)
                slot = entries.setdefault(key, {})
                for iface, instance in interfaces:
                    slot.setdefault(iface, set()).add(instance)
    return entries, files


def render(entries):
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<compatibility-matrix version="%s" type="framework">' % MATRIX_VERSION,
        "    <!-- %s -->" % PROVENANCE,
    ]
    for (fmt, name, versions) in sorted(entries):
        lines.append('    <hal format="%s" optional="true">' % fmt)
        lines.append("        <name>%s</name>" % name)
        for version in versions:
            lines.append("        <version>%s</version>" % version)
        by_iface = entries[(fmt, name, versions)]
        for iface in sorted(by_iface, key=lambda x: (x or "")):
            lines.append("        <interface>")
            if iface is not None:
                lines.append("            <name>%s</name>" % iface)
            for instance in sorted(by_iface[iface]):
                lines.append("            <instance>%s</instance>" % instance)
            lines.append("        </interface>")
        lines.append("    </hal>")
    lines.append("</compatibility-matrix>")
    lines.append("")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest-dir",
        action="append",
        required=True,
        help="Directorio etc/vintf con manifiestos (repetible).",
    )
    parser.add_argument("-o", "--output", required=True, help="Archivo de salida.")
    args = parser.parse_args(argv)

    entries, files = collect(args.manifest_dir)
    if not files:
        raise SystemExit("No se encontro ningun manifiesto en: %s"
                         % ", ".join(args.manifest_dir))
    text = render(entries)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(text.encode("utf-8"))

    hals = len(entries)
    interfaces = sum(len(v) for v in entries.values())
    print("manifiestos: %d | hal (nombre+versiones): %d | interfaces: %d | -> %s"
          % (files, hals, interfaces, out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
