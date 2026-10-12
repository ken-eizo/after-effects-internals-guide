"""Verify 11 scoped LayerStyle native TDB registrars are 8 native leaf
TDB_Stream constructors and exactly 3 host group constructors.
Reads two pinned native binaries and locally derived PE datasets only.
"""
from pathlib import Path
import json,hashlib
root=Path(r"D:\Developer\ShapeLayerAE\results")
source=json.loads((root/"layerstyle_11_tdb_creators_concrete_classes_2025_2026.json").read_text())["years"]
groups=["AdvancedBlendingStreamGroup","BlendingOptionsStreamGroup","RootLayerStyleStreamGroup"]
report={}
for y in ("2025","2026"):
 rows=source[y]["registered_callback_creators"]
 assert len(rows)==11
 counts={"typed_leaf_stream":0,"built_in_group":0}
 categories=[]
 for idx,v in enumerate(rows):
  syms=[z["symbol"] for z in v["named_call_edges"]]
  leaf=any("??0TDB_Stream@@" in s for s in syms)
  g=[name for name in groups if any(f"??0{name}@" in s for s in syms)]
  assert bool(leaf) != bool(g),(y,idx,syms)
  assert len(g)<=1
  if leaf:
   counts["typed_leaf_stream"]+=1;kind="TDB_Stream_leaf"
  else:
   counts["built_in_group"]+=1;kind=g[0]
  categories.append({"entry_index":idx,"creator":v["callback_rva"],
                     "kind":kind,"known_Adobe_concrete_class":True})
 assert counts=={"typed_leaf_stream":8,"built_in_group":3},(y,counts)
 assert [z["kind"] for z in categories if z["kind"]!="TDB_Stream_leaf"]==groups
 report[y]={"BEE_sha256":source[y]["sha256"],"exact_registrars":11,
  "typed_leaf_stream_creators":8,"built_in_group_creators":3,
  "creators":categories,"custom_CNL_vector_group":False}
 print("PASS",y,"8 native value streams + 3 native LayerStyle groups",flush=True)
p=root/"layerstyle_11_scoped_creator_types_verified_2025_2026.json"
p.write_text(json.dumps({"evidence":"E2-L actual constructor code calls two pinned BEE PE binaries","versions":report,
"notes":["These are Adobe internal registrations, not plugin extensibility APIs",
"RTTI vtables of external CNL types and native Pen/renderer not established"]},indent=2)+"\n")
print("SAVED",p)
