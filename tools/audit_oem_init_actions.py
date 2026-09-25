#!/usr/bin/env python3
"""Summarize OEM init action blocks against a selected ROM builtin name table.

Static name comparison only; never executes actions or approves their semantics.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shlex


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('oem_rc', type=Path)
    p.add_argument('rom_builtins', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    if a.output.exists():
        p.error('output exists; refuse overwrite')
    raw = a.oem_rc.read_bytes()
    source = a.rom_builtins.read_bytes()
    text = source.decode('utf-8')
    start = text.index('static const BuiltinFunctionMap builtin_functions = {')
    end = text.index('\n    };', start)
    supported = set(re.findall(r'\{\s*"([a-z_]+)"\s*,', text[start:end]))
    if not {'mkdir', 'write', 'mount', 'trigger', 'setprop'}.issubset(supported):
        raise ValueError('unexpected builtin map format')
    blocks, unsupported, counts, errors = [], [], Counter(), []
    current = None
    pending = ''
    for number, line in enumerate(raw.decode('utf-8').splitlines(), 1):
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
            errors.append({'line': first, 'reason': str(error)})
            current = None
            continue
        if not tokens:
            continue
        if tokens[0] in ('on', 'service', 'import'):
            current = None
            if tokens[0] == 'on':
                current = {'line': first, 'trigger': line.strip()[3:], 'command_count': 0, 'commands': {}}
                blocks.append(current)
            continue
        if current is None:
            continue
        command = tokens[0]
        counts[command] += 1
        current['command_count'] += 1
        current['commands'][command] = current['commands'].get(command, 0) + 1
        if command not in supported:
            unsupported.append({'line': first, 'command': command, 'trigger': current['trigger']})
    if pending:
        errors.append({'line': first, 'reason': 'unfinished continuation'})
    result = {'schema_version': 1, 'created_utc': datetime.now(timezone.utc).isoformat(),
              'oem_file': a.oem_rc.name, 'oem_sha256': hashlib.sha256(raw).hexdigest(),
              'rom_builtins_sha256': hashlib.sha256(source).hexdigest(),
              'rom_builtin_names': sorted(supported), 'action_blocks': blocks,
              'command_counts': dict(sorted(counts.items())), 'commands_absent_from_rom_map': unsupported,
              'parse_limits_or_errors': errors,
              'limits': ['Only action command names compared, not argument arity, SELinux permissions or execution',
                         'Service definitions and imports not interpreted by this tool',
                         'Presence of an OEM action does not establish a ROM requirement',
                         'No changes to the phone, stock rc or build activation']}
    with a.output.open('x', encoding='utf-8', newline='\n') as out:
        json.dump(result, out, indent=2)
        out.write('\n')
    print(json.dumps({'action_blocks': len(blocks), 'commands': sum(counts.values()),
                      'unsupported_names': unsupported, 'parse_limits_or_errors': errors}))


if __name__ == '__main__':
    main()
