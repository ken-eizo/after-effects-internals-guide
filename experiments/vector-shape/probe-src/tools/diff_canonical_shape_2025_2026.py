from pathlib import Path
import json,collections
p=Path(__file__).resolve().parents[4]/"datasets"/"ae-bee-canonical-grammar-strict-rdx-2025-2026.json"
data=json.loads(p.read_text(encoding="utf-8"))
x={k:[c["child_symbol"] for c in g["identified_canonical_children"]] for k,g in data["2025"]["groups"].items()}
y={k:[c["child_symbol"] for c in g["identified_canonical_children"]] for k,g in data["2026"]["groups"].items()}
diff=[]
for group in sorted(set(x)|set(y)):
 old=set(x.get(group,[]));new=set(y.get(group,[]))
 if old!=new:
  diff.append({"class":group,"added_2026":sorted(new-old),"removed_2026":sorted(old-new),"common":len(new&old),"2025_count":len(old),"2026_count":len(new)})
print("GROUP CLASS DIFF",len(diff))
for d in diff:print(d)
parent="VectorsStreamGroup@BEE_VectorStream"
print("SHAPE canonical item order 2025",x[parent])
print("SHAPE canonical item order 2026",y[parent])
import hashlib
print("SHA",hashlib.sha256(p.read_bytes()).hexdigest())
path=Path(__file__).resolve().parents[4]/"datasets"/"ae-bee-canonical-grammar-2025-2026-diff.json"
result={"schema":"strict-RDX direct registered canonical match names only",
 "total_2025":data["2025"]["identified_canonical_edges"],"total_2026":data["2026"]["identified_canonical_edges"],
 "all_calls_2025":sum(g["canonical_lookup_calls"] for g in data["2025"]["groups"].values()),
 "all_calls_2026":sum(g["canonical_lookup_calls"] for g in data["2026"]["groups"].values()),
 "shape_contents_children_2025":x[parent],"shape_contents_children_2026":y[parent],
 "group_differences":diff}
path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("SAVED",path)
