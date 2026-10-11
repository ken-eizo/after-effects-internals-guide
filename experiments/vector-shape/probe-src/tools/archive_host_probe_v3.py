"""Archive fresh EXP-SHAPE-009/010 host v3 traces without mutating AE state."""
from pathlib import Path
from datetime import datetime
import csv,json,hashlib,os,collections,subprocess
src=Path(os.environ["TEMP"])
root=Path(r"D:\Developer\After Effects Internals Guide")
dst=root/"experiments"/"vector-shape"/"runs"/"EXP-SHAPE-009-010"/"20261011-user-host-v3"
dst.mkdir(parents=True,exist_ok=True)
names=["ShapeLayerAE_stream_tree.tsv","ShapeLayerAE_stream_metadata.tsv","ShapeLayerAE_canadd.tsv","ShapeLayerAE_canadd_unknown.tsv","ShapeLayerAE_private_factory_probe.tsv"]
o={"date":"2026-10-11","host":"AE 2026","experiment_ids":["EXP-SHAPE-009","EXP-SHAPE-010"],"source_temp_directory":str(src),"files":[]}
tables={}
for name in names:
    p=src/name
    raw=p.read_bytes()
    (dst/name).write_bytes(raw)
    header=[x for x in raw.decode("utf-8-sig","replace").splitlines() if x and not x.startswith("#")]
    rows=list(csv.DictReader(header,delimiter="\t"))
    tables[name]=rows
    o["files"].append({"name":name,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"rows":len(rows),"last_modified_local":datetime.fromtimestamp(p.stat().st_mtime).isoformat()})
m=tables["ShapeLayerAE_stream_metadata.tsv"]
o["metadata"]={
"rows":len(m),
"uid_distribution":dict(collections.Counter(r["unique_stream_id"] for r in m)),
"uid_second_call_distribution":dict(collections.Counter(r["uid_second_call"] for r in m)),
"uid_error_distribution":dict(collections.Counter(r["uid_error"] for r in m)),
"second_uid_error_distribution":dict(collections.Counter(r["second_uid_error"] for r in m)),
"two_call_discrepancy_count":sum(r["unique_stream_id"]!=r["uid_second_call"] for r in m),
"depth_mismatch_count":sum(int(r["depth"])!=int(r["sdk_depth"]) for r in m)}
o["factory_getter"]=tables["ShapeLayerAE_private_factory_probe.tsv"]
o["canadd_unknown"]={
"total":len(tables["ShapeLayerAE_canadd_unknown.tsv"]),
"by_candidate":{},
"error_distribution":dict(collections.Counter(r["query_error"] for r in tables["ShapeLayerAE_canadd_unknown.tsv"]))}
for r in tables["ShapeLayerAE_canadd_unknown.tsv"]:
    o["canadd_unknown"]["by_candidate"].setdefault(r["candidate_match_name"],collections.Counter())[r["parent_match_name"]+":"+r["can_add"]]+=1
o["canadd_unknown"]["by_candidate"]={k:dict(v) for k,v in o["canadd_unknown"]["by_candidate"].items()}
(dst/"analysis.json").write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("ARCHIVED",dst)
for info in o["files"]:print(" FILE",info)
print("UID",o["metadata"])
print("FACTORY",o["factory_getter"])
print("UNKNOWN",json.dumps(o["canadd_unknown"],ensure_ascii=False)[:4500])
