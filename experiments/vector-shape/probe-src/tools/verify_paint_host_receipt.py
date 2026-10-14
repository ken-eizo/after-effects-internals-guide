from pathlib import Path
import csv,hashlib,json
ROOT=Path(__file__).resolve().parents[4]
rawpath=ROOT/'datasets'/'ae-paint-native-hierarchy-host-2026-20261014.tsv'
jsonpath=ROOT/'datasets'/'ae-paint-native-hierarchy-host-2026-20261014-summary.json'
raw=rawpath.read_bytes()
meta=json.loads(jsonpath.read_text(encoding='utf8'))
assert hashlib.sha256(raw).hexdigest()==meta['source_sha256']
rows=list(csv.reader(raw.decode('utf-8-sig').splitlines(),delimiter='\t'))
table={}
for row in rows:
 if row:table.setdefault(row[0],[]).append(row[1:])
kv={k:v[0][0] for k,v in table.items() if k not in ('node','can_add','effect_instance') and len(v)==1}
assert kv['paint_found']=='1'
assert int(kv['errors'])==meta['error_count']==0
assert int(kv['inspected_nodes'])==len(table['node'])==meta['inspected_nodes']==35
assert kv['host_project_mutated']=='0' and kv['private_host_calls']=='0'
assert len(table['can_add'])==6
can={}
for r in table['can_add']:
 assert len(r)==4
 parent,child,value,err=r
 assert parent.endswith('/ADBE Paint Group')
 assert int(err)==0
 can[child]=bool(int(value))
assert can['ADBE Paint Atom'] is True
for name in ['ADBE Paint Nibbler Atom','ADBE Paint Shape','ADBE Vector Group','CNL:PaintAtom','ADBE Paint Atom - CNLProbe']:
 assert can[name] is False
nodes={r[2]:r for r in table['node']}
for n,k,count in [('ADBE Paint',1,4),('ADBE Paint Group',2,1),('ADBE Paint Atom',1,6),('ADBE Paint Properties',1,16),('ADBE Paint Transform',1,4),('ADBE Paint Nibbler Group',2,0)]:
 r=nodes[n]
 assert int(r[4])==k and int(r[5])==count,(n,r)
assert all(list(map(int,r[-4:]))==[0]*4 for r in table['node'])
assert meta['can_add_matrix']['CNL:PaintAtom']['can_add']==0
print('PASS host Paint native hierarchy SHA, 35 nodes, zero errors, parent type counts, 6 CanAdd matrix rows')
print('SAFETY: no private calls or host modifications reported; foreign Stream registration NOT PROVEN')
