"""Capture user-run v2 AEGP experiment and reproduce statistics.
NEVER modify the running AE session.
"""
from pathlib import Path
from datetime import datetime
import csv,json,hashlib,collections,os
root=Path(r"D:\Developer\After Effects Internals Guide")
source=Path(os.environ["TEMP"])
d=root/"experiments"/"vector-shape"/"runs"/"EXP-SHAPE-005"/"20261011-user-host-v2"
d.mkdir(parents=True,exist_ok=True)
names=["ShapeLayerAE_stream_tree.tsv","ShapeLayerAE_stream_metadata.tsv","ShapeLayerAE_canadd.tsv"]
stats={"experiment_id":"EXP-SHAPE-005","host":"Adobe After Effects 2026","captured_file_info":[]}
tables={}
for name in names:
    p=source/name
    blob=p.read_bytes()
    (d/name).write_bytes(blob)
    rows=list(csv.DictReader([x for x in blob.decode("utf-8-sig","replace").splitlines() if x and not x.startswith("#")],delimiter="\t"))
    tables[name]=rows
    stats["captured_file_info"].append({"name":name,"bytes":len(blob),"sha256":hashlib.sha256(blob).hexdigest(),"rows":len(rows),"last_modified_local":datetime.fromtimestamp(p.stat().st_mtime).isoformat()})
meta=tables["ShapeLayerAE_stream_metadata.tsv"]
tree=tables["ShapeLayerAE_stream_tree.tsv"]
caps=tables["ShapeLayerAE_canadd.tsv"]
stats["metadata"]={
    "n":len(meta),
    "unique_stream_id_distribution":dict(collections.Counter(r["unique_stream_id"] for r in meta)),
    "uid_api_error_distribution":dict(collections.Counter(r["uid_error"] for r in meta)),
    "depth_mismatch_count":sum(int(r["sdk_depth"])!=int(r["depth"]) for r in meta),
    "grouping_counts":dict(collections.Counter(r["grouping"] for r in meta)),
    "modified_count":sum(int(r["is_modified"]) for r in meta),
    "flag_common":dict(collections.Counter(r["dynamic_flags"] for r in meta)),
    "nonzero_any_api_error":sum(any(int(r[k])!=0 for k in ("uid_error","depth_error","flags_error","other_error")) for r in meta)
}
stats["tree"]={"rows":len(tree),"max_depth":max(int(x["depth"]) for x in tree),"errors":dict(collections.Counter(x["aegp_error"] for x in tree))}
byparent=collections.defaultdict(dict)
for row in caps:
    byparent[row["parent_match_name"]][row["candidate_match_name"]]={"allowed":int(row["can_add"]),"error":int(row["query_error"])}
stats["canadd"]={"rows":len(caps),"parents":{k:v for k,v in byparent.items()},
                "errors":dict(collections.Counter(r["query_error"] for r in caps)),
                "distinct_parent_uid_values":sorted(set(r["parent_stream_uid"] for r in caps))}
(d/"analysis.json").write_text(json.dumps(stats,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("ARCHIVED",d)
print("FILES",json.dumps(stats["captured_file_info"],ensure_ascii=False))
print("METADATA",stats["metadata"])
print("CANADD",json.dumps(stats["canadd"],ensure_ascii=False))
