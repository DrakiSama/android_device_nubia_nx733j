#!/usr/bin/env python3
"""Audit captured ARM64 module metadata; never load modules or extract paths.
Usage: audit_kernel_modules.py RAMDISK_LZ4 REFERENCE_JSON PROC_MODULES OUTPUT_JSON
Requires lz4. Checks captured hashes and imported CRC consistency, not kernel ABI.
"""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys


def cpio_entries(data):
    offset=0
    while offset+110 <= len(data):
        header=data[offset:offset+110]
        if header[:6] != b'070701':
            raise ValueError('requires newc CPIO without checksum')
        fields=[int(header[6+i*8:14+i*8],16) for i in range(13)]
        size,namesize=fields[6],fields[11]
        offset+=110
        if namesize < 1 or offset+namesize > len(data):
            raise ValueError('invalid CPIO name')
        rawname=data[offset:offset+namesize]
        if rawname[-1:] != b'\0':
            raise ValueError('unterminated CPIO name')
        name=rawname[:-1].decode()
        offset=(offset+namesize+3)&~3
        body=data[offset:offset+size]
        if len(body)!=size:
            raise ValueError('truncated CPIO member')
        offset=(offset+size+3)&~3
        if name=='TRAILER!!!': return
        yield name,body
    raise ValueError('missing CPIO trailer')


def module_metadata(data):
    if len(data)<64 or data[:6]!=b'\x7fELF\x02\x01':
        raise ValueError('requires ELF64 little-endian')
    if struct.unpack_from('<HH',data,16)!=(1,183):
        raise ValueError('requires AArch64 relocatable module')
    table=struct.unpack_from('<Q',data,40)[0]
    entsize,count,names=struct.unpack_from('<HHH',data,58)
    if entsize<64 or not 0<names<count or table+entsize*count>len(data):
        raise ValueError('invalid section table')
    sections=[struct.unpack_from('<IIQQQQIIQQ',data,table+i*entsize) for i in range(count)]
    def contents(section):
        offset,size=section[4:6]
        if offset+size>len(data): raise ValueError('section out of bounds')
        return data[offset:offset+size]
    names_data=contents(sections[names])
    selected={}
    for section in sections:
        at=section[0]
        end=names_data.find(b'\0',at)
        if at>=len(names_data) or end<0:raise ValueError('invalid section name')
        name=names_data[at:end].decode()
        if name in ('.modinfo','__versions'):selected[name]=contents(section)
    if '.modinfo' not in selected:raise ValueError('missing module info')
    metadata={}
    for field in selected['.modinfo'].split(b'\0'):
        if b'=' in field:
            key,value=field.split(b'=',1)
            metadata.setdefault(key.decode(),[]).append(value.decode())
    versions=selected.get('__versions',b'')
    if len(versions)%64:raise ValueError('unexpected basic modversions record size')
    crcs={}
    for start in range(0,len(versions),64):
        value=struct.unpack_from('<Q',versions,start)[0]
        name=versions[start+8:start+64].split(b'\0',1)[0].decode()
        if not name:raise ValueError('empty versioned symbol')
        if name in crcs and crcs[name]!=value:raise ValueError('conflicting version records')
        crcs[name]=value
    return metadata,crcs


def audit(ramdisk,reference,loaded_text):
    expected={row['path']:row for row in reference}
    loaded={line.split()[0] for line in loaded_text.splitlines() if line.strip()}
    records=[]
    imports={}
    seen=set()
    for path,data in cpio_entries(ramdisk):
        if not path.endswith('.ko'):continue
        if path in seen:raise ValueError('duplicate module path')
        seen.add(path)
        digest=hashlib.sha256(data).hexdigest()
        if path not in expected or digest!=expected[path]['sha256']:
            raise ValueError('module hash differs from reference: '+path)
        meta,crcs=module_metadata(data)
        name=meta.get('name',[Path(path).stem.replace('-','_')])[0]
        records.append({'path':path,'name':name,'sha256':digest,
            'vermagic':meta.get('vermagic',[]),'srcversion':meta.get('srcversion',[]),
            'depends':meta.get('depends',[]),'versioned_imports':len(crcs),
            'name_observed_loaded':name in loaded})
        for symbol,crc in crcs.items():
            imports.setdefault(symbol,{}).setdefault(f'{crc:08x}',[]).append(name)
    if seen!=set(expected):raise ValueError('missing reference modules')
    conflicts={name:values for name,values in sorted(imports.items()) if len(values)>1}
    return {'schema_version':1,'captured_modules':len(records),'hashes_match_reference':True,
        'loaded_module_names':len(loaded),'captured_names_observed_loaded':sum(r['name_observed_loaded'] for r in records),
        'unique_versioned_imports':len(imports),'import_crc_conflicts':conflicts,
        'modules_without_versioned_imports':[r['path'] for r in records if not r['versioned_imports']],
        'modules':records,'limits':['Loaded name matching is not proof of loaded bytes or runtime integrity.',
            'Import CRC agreement between modules is not agreement with kernel export CRCs.',
            'Kernel export ABI, signature acceptance and replacement kernel compatibility remain unverified.']}


def main():
    if len(sys.argv)!=5:raise SystemExit(__doc__)
    ramdisk=subprocess.check_output(['lz4','-dc',sys.argv[1]])
    report=audit(ramdisk,json.loads(Path(sys.argv[2]).read_text()),Path(sys.argv[3]).read_text())
    Path(sys.argv[4]).write_bytes((json.dumps(report,indent=2)+'\n').encode())
    for key in ('captured_modules','loaded_module_names','captured_names_observed_loaded','unique_versioned_imports'):
        print(key,report[key])
    print('CRC conflicts',len(report['import_crc_conflicts']))

if __name__=='__main__':main()