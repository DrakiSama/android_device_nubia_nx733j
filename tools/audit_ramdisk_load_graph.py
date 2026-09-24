#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,fnmatch,argparse
parser=argparse.ArgumentParser(description='Read-only static audit of ramdisk load metadata; does not establish runtime ordering.')
parser.add_argument('metadata',type=Path)
parser.add_argument('reference',type=Path)
parser.add_argument('output',type=Path)
args=parser.parse_args()
if args.output.exists():parser.error('output exists; choose a new report path')
root=args.metadata
ref=json.loads(args.reference.read_text())
modules={r['path'][len('modules/'):]:r for r in ref['modules'] if r['path'].startswith('modules/vendor_boot/')}
by_name={Path(p).stem.replace('-','_'):p for p in modules};by_file={Path(p).name:p for p in modules}
if len(by_name)!=len(modules):raise ValueError('ambiguous canonical module names')
def resolve(name):
    if name in by_file:return by_file[name]
    return by_name.get(Path(name).name.removesuffix('.ko').replace('-','_'))
def lines(name):return [s.split('#',1)[0].strip() for s in (root/name).read_text().splitlines() if s.split('#',1)[0].strip()]
hard={};unknown=[]
for line in lines('modules.dep'):
    source,deps=line.split(':',1);p=resolve(source)
    if not p or p in hard:raise ValueError('invalid or repeated modules.dep entry')
    hard[p]=set()
    for token in deps.split():
        target=resolve(token)
        if target:hard[p].add(target)
        else:unknown.append({'source':source,'dependency':token})
assert set(hard)==set(modules)
soft=[]
for line in lines('modules.softdep'):
    words=line.split();assert words[0]=='softdep';rule={'module':words[1],'path':resolve(words[1]),'pre':[],'post':[]};mode=None
    for word in words[2:]:
        if word in ('pre:','post:'):mode=word[:-1]
        else:
            assert mode;rule[mode].append({'name':word,'path':resolve(word)})
    soft.append(rule)
aliases=[]
for line in lines('modules.alias'):
    directive,pattern,target=line.split();assert directive=='alias';aliases.append({'pattern':pattern,'target':target,'path':resolve(target)})
blocks=[]
for line in lines('modules.blocklist'):
    directive,name=line.split();assert directive=='blocklist';blocks.append(name.replace('-','_'))
initial=[resolve(name) for name in lines('modules.load')];assert all(initial) and len(set(initial))==len(initial)
selected=set(initial);closure=set(initial)
while True:
    expanded=set(closure)
    for p in closure:expanded.update(hard[p])
    for rule in soft:
        if rule['path'] in closure:expanded.update(r['path'] for r in rule['pre']+rule['post'] if r['path'])
    if expanded==closure:break
    closure=expanded
# Edges are prerequisite -> consumer; postdeps reverse that direction.
edges=set()
for p in closure:
    for d in hard[p]:edges.add((d,p))
active=[]
for rule in soft:
    if rule['path'] not in closure:continue
    active.append(rule)
    for x in rule['pre']:
        if x['path']:edges.add((x['path'],rule['path']))
    for x in rule['post']:
        if x['path']:edges.add((rule['path'],x['path']))
remaining=set(closure);layers=[]
while remaining:
    ready=sorted(p for p in remaining if not any(b==p and a in remaining for a,b in edges))
    if not ready:break
    layers.append(ready);remaining.difference_update(ready)
positions={p:i+1 for i,p in enumerate(initial)}
forward=[{'prerequisite':a,'consumer':b,'prerequisite_line':positions[a],'consumer_line':positions[b]} for a,b in sorted(edges) if a in positions and b in positions and positions[a]>positions[b]]
report={'schema_version':1,'source':'NX733J vendor_boot B ramdisk metadata','metadata_sha256':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ('modules.dep','modules.softdep','modules.alias','modules.blocklist','modules.load')},'module_files':len(modules),'dep_entries':len(hard),'dep_unknown_targets':unknown,'softdep_rules':len(soft),'normal_active_softdeps':active,'alias_entries':len(aliases),'aliases_with_missing_target':[r for r in aliases if not r['path']],'normal_explicit_entries_matching_alias_patterns':[{'entry':name,'pattern':a['pattern'],'target':a['target']} for name in lines('modules.load') for a in aliases if fnmatch.fnmatchcase(name.removesuffix('.ko').replace('-','_'),a['pattern'])],'blocklist_entries':len(blocks),'blocklist_unique_names':len(set(blocks)),'normal_blocklisted_modules':sorted(p for p in closure if modules[p]['name'] in blocks),'normal_initial_modules':len(initial),'normal_hard_and_soft_closure':len(closure),'normal_added_modules':sorted(closure-selected),'normal_unknown_softdep_targets':[x for r in active for x in r['pre']+r['post'] if not x['path']],'combined_graph_edges':len(edges),'topological_layers':layers,'unresolved_topological_nodes':sorted(remaining),'prerequisites_after_consumer_in_text':forward,'limits':['Topological layers describe declared constraints, not observed execution times.','Aliases are checked structurally and against explicit normal-load names, not against every live device modalias.','No assertion about stock loader implementation or successful insertion is derived from this graph.']}
with args.output.open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(json.dumps(report,indent=2)+'\n')
for k in ('module_files','dep_entries','dep_unknown_targets','softdep_rules','alias_entries','aliases_with_missing_target','normal_explicit_entries_matching_alias_patterns','normal_blocklisted_modules','normal_initial_modules','normal_hard_and_soft_closure','normal_added_modules','normal_unknown_softdep_targets','combined_graph_edges','unresolved_topological_nodes'):print(k,report[k])
print('Normal active softdeps',len(active));print('Prerequisites after consumer in text',len(forward));print('Topological layers',len(layers))

if unknown or report['normal_unknown_softdep_targets'] or report['normal_blocklisted_modules'] or remaining:
    raise SystemExit(2)
