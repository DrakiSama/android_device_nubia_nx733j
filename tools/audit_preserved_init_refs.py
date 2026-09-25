#!/usr/bin/env python3
"""Inventory literal service executables outside preserved vendor, not load order.

Only service declarations and selected options are parsed. This does not evaluate
init imports, property triggers, overrides, scripts or linker namespaces.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('vendor', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    if a.output.exists():
        p.error('output exists; refuse overwrite')
    root = a.vendor / 'etc/init'
    if not root.is_dir():
        p.error('vendor/etc/init is absent')
    files, services, aliases, errors = {}, [], [], []
    for path in sorted(root.rglob('*.rc')):
        if path.is_symlink():
            errors.append({'file': path.relative_to(a.vendor).as_posix(), 'reason': 'symlink not followed'})
            continue
        rel = 'vendor/' + path.relative_to(a.vendor).as_posix()
        data = path.read_bytes()
        files[rel] = hashlib.sha256(data).hexdigest()
        current, pending, first = None, '', 0
        for number, line in enumerate(data.decode('utf-8').splitlines(), 1):
            if not pending:
                first = number
            if line.endswith('\\'):
                pending += line[:-1] + ' '
                continue
            line = pending + line
            pending = ''
            try:
                tokens = shlex.split(line, comments=True, posix=True)
            except ValueError as error:
                errors.append({'file': rel, 'line': first, 'reason': str(error)})
                current = None
                continue
            if not tokens:
                continue
            if tokens[0] in ('on', 'import', 'service'):
                current = None
            if tokens[0] == 'service' and len(tokens) >= 3:
                exe = tokens[2]
                args = [x for x in tokens[3:] if x.startswith(('/system/', '/system_ext/', '/product/'))
                        and not x.startswith('/system/vendor/')]
                if exe.startswith('/system/vendor/'):
                    aliases.append({'file': rel, 'line': first, 'service': tokens[1], 'executable': exe,
                                    'classification': 'requires /system/vendor alias; not assumed external'})
                elif exe.startswith(('/system/', '/system_ext/', '/product/')) or args:
                    current = {'file': rel, 'line': first, 'service': tokens[1], 'executable': exe,
                               'literal_external_arguments': args, 'options': []}
                    services.append(current)
            elif current is not None and tokens[0] in ('class', 'disabled', 'oneshot', 'critical', 'override', 'user', 'group'):
                current['options'].append(tokens)
        if pending:
            errors.append({'file': rel, 'line': first, 'reason': 'unfinished continuation'})
    report = {'schema_version': 1, 'created_utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'literal service declarations in extracted stock vendor/etc/init',
              'files_sha256': files, 'external_service_declarations': services,
              'system_vendor_alias_declarations': aliases, 'parse_limits_or_errors': errors,
              'limits': ['Declarations do not prove active imports or actual service execution',
                         'Duplicate names and overrides require separate resolution',
                         'Only selected options retained; not a complete Android init parser',
                         'No package selected for installation; no hardware subsystem ported']}
    with a.output.open('x', encoding='utf-8', newline='\n') as out:
        json.dump(report, out, indent=2)
        out.write('\n')
    print(json.dumps({'files': len(files), 'external_declarations': len(services),
                      'alias_declarations': len(aliases), 'parse_limits_or_errors': errors}))


if __name__ == '__main__':
    main()
