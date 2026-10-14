"""Verify a frozen *real AE2026* v2 native Paint inspection receipt.
No connection to AE required, no private ABI or project writes.
"""
from pathlib import Path
import hashlib,collections,csv,json
root=Path(__file__).resolve().parents[4]
data=root/"datasets"
p=data/"ae-paint-native-hierarchy-host-v2-2026-20261014.tsv"
m=data/"ae-paint-native-hierarchy-host-v2-2026-20261014-summary.json"
raw=p.read_bytes()
summary=json.loads(m.read_text(encoding="utf8"))
assert hashlib.sha256(raw).hexdigest()==summary["source_sha256"]
rows=list(csv.reader(raw.decode("utf-8-sig").splitlines(),delimiter="\t"))
types=collections.defaultdict(list)
for r in rows:
 if r:types[r[0]].append(r)
kv={r[0]:r[1] for r in rows if len(r)>1 and r[0] not in ("node","can_add","leaf_meta","effect_instance")}
assert kv["format"].endswith("v2")
assert kv["paint_found"]=="1"
assert kv["host_project_mutated"]==kv["private_host_calls"]=="0"
for k in ("errors","metadata_query_errors"):
 assert kv[k]=="0"
assert int(kv["inspected_nodes"])==len(types["node"])==summary["native_stream_node_count"]==170
assert int(kv["metadata_leaves"])==len(types["leaf_meta"])==summary["leaf_value_metadata_count"]==142
brushes=[r for r in types["node"] if len(r)>3 and r[3]=="ADBE Paint Atom"]
assert len(brushes)==summary["brush_stroke_count"]==6
assert len(types["can_add"])==6
matrix={r[2]:bool(int(r[3])) for r in types["can_add"]}
assert matrix["ADBE Paint Atom"]
assert sum(matrix.values())==1 and not matrix["CNL:PaintAtom"]
leaves=[]
for r in types["leaf_meta"]:
 assert len(r)==11
 path,typ,can,vary,data,keys,*errs=r[1:]
 assert all(int(x)==0 for x in errs)
 leaves.append((path.split("/")[-1],int(typ),int(can),int(vary),int(keys)))
hist=dict(sorted(collections.Counter(x[1] for x in leaves).items()))
assert {str(k):v for k,v in hist.items()}==summary["leaf_stream_type_histogram"]
assert sum(vary for *_,vary,keys in leaves)==0
assert sum(can for name,typ,can,vary,keys in leaves)==109
assert all(keys<=0 for name,typ,can,vary,keys in leaves)
path_leaves=[r for r in leaves if r[0]=="ADBE Paint Shape"]
assert len(path_leaves)==6 and all(typ==0 and can for name,typ,can,vary,keys in path_leaves)
print("PASS host AE2026 Paint v2: SHA verified, 6 brushes, 170 native streams, 142 leaf metadata, 109 animatable, 0 errors")
print("Paint Path public value type NO_DATA (0) in all six Brush instances; this is not absence of a host-native Path.")
print("Unknown external CNL Stream name denied; plugin native custom Stream registration NOT achieved.")
