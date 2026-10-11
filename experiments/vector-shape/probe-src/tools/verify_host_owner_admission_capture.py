"""Validate user AE2026 AEGP read-only native owner scan.
Privacy: only emit aggregate counts, no individual project/plugin names.
"""
import os,json
from pathlib import Path
from collections import Counter
p=Path(os.environ["TEMP"])/"CNL_NativeOwner_Admission.tsv"
rows=[]
for line in p.read_text(encoding="utf-8-sig").splitlines():
 if line.startswith("#") or not line.strip():continue
 rows.append(line.split("\t"))
def one(name):
 x=[r for r in rows if r[0]==name]
 assert len(x)==1,(name,len(x))
 return x[0][1]
stream={int(r[1]):r for r in rows if r[0]=="stream"}
parent={int(r[1]):int(r[2]) for r in rows if r[0]=="parent_link"}
groups={int(r[1]):r for r in rows if r[0]=="group"}
admission=[r for r in rows if r[0]=="admission"]
assert one("root_stream_error")=="0"
assert one("layer_object_type")=="4"
assert one("host_stream_tree_is_readonly")=="1"
assert one("stream_created")=="0" and one("private_registry_invoked")=="0"
assert int(one("visited_nodes"))==len(stream)==len(parent)
assert len(groups)*6==len(admission)
assert set(parent)==set(stream)
assert any(r[4]=="ADBE Root Vectors Group" for r in stream.values())
assert any(r[4]=="ADBE Effect Parade" for r in stream.values())
def outcome(container,child):
 nodes={i for i,r in stream.items() if r[4]==container}
 return [r for r in admission if int(r[1]) in nodes and r[2]==child]
def success(rows):
 return any(r[3]=="1" and r[4]=="0" for r in rows)
assert success(outcome("ADBE Root Vectors Group","ADBE Vector Graphic - Fill"))
assert success(outcome("ADBE Root Vectors Group","ADBE Vector Filter - Trim"))
assert success(outcome("ADBE Effect Parade","ADBE Slider Control"))
cnl=[r for r in admission if r[2]=="CNL Native Independent Group"]
assert len(cnl)==len(groups)
assert all(r[3]=="0" and r[4]=="0" for r in cnl)
report={
 "classification":"AE2026 user host-tested PUBLIC READ-ONLY API; bounded scan; no private calls",
 "data_minimization":"host/project/effect names not included; only standard Adobe type names in assertions",
 "layer_object_type":int(one("layer_object_type")),
 "root_stream_error":0,
 "visited_nodes":len(stream),"tested_groups":len(groups),
 "admission_queries":len(admission),
 "max_observed_depth":max(int(r[2]) for r in stream.values()),
 "positive_admissions":sum(r[3]=="1" and r[4]=="0" for r in admission),
 "cnl_matchname_positive_admissions":0,
 "cnl_matchname_negative_admissions":len(cnl),
 "positive_controls":{"root_vectors_fill":True,"root_vectors_trim":True,"effect_parade_slider":True},
 "private_registry_invoked":False,"host_stream_created":False,
 "limitations":["per-parent AddStream admission only; no instance creation attempted",
  "unregistered MatchName may fail even where a registered instance could differ",
  "stream traversal bounded: max depth 4, max nodes 240",
  "selected Shape Layer only; does not establish arbitrary AV effect behavior"]
}
dst=Path(r"D:\Developer\ShapeLayerAE\results\ae2026_owner_admission_host_aggregate_20261012.json")
dst.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("PASS HOST ACTUAL OWNER DATA",json.dumps(report,ensure_ascii=False))
print("SAVED",dst)
