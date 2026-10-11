"""Preserve and analyze the user-produced in-host ShapeLayerAE stream-tree TSV.
No AE session changes. Validated E2-X host capture, scoped to this single layer.
"""
from pathlib import Path
import os,json,csv,hashlib,collections,subprocess,platform,datetime
src=Path(os.environ["TEMP"])/"ShapeLayerAE_stream_tree.tsv"
root=Path(r"D:\Developer\After Effects Internals Guide")
dst=root/r"experiments\vector-shape\runs\EXP-SHAPE-001\20261011-first-success"
dst.mkdir(parents=True,exist_ok=True)
data=src.read_bytes()
(dst/"shape_layer_stream_tree.tsv").write_bytes(data)
rows=list(csv.DictReader((line for line in data.decode("utf-8-sig","replace").splitlines() if line and not line.startswith("#")),delimiter="\t"))
summary={
"experiment_id":"EXP-SHAPE-001",
"reported_host_build":"After Effects 2026 (host executable D:/Adobe/Adobe After Effects 2026/Support Files/AfterFX.exe)",
"host_runtime_version":"not obtained via AEGP version suite in this run",
"host_process_start":"2026-10-11 17:44:42 local (reported by Get-Process)",
"source_capture_last_modified":"2026-10-11 17:46:29 local",
"capture_source":str(src),"archived_relative":"shape_layer_stream_tree.tsv",
"source_sha256":hashlib.sha256(data).hexdigest(),
"row_count":len(rows),
"group_counts":dict(collections.Counter(row["grouping"] for row in rows)),
"error_counts":dict(collections.Counter(row["aegp_error"] for row in rows)),
"max_depth":max(int(row["depth"]) for row in rows),
"match_name_counts":dict(collections.Counter(row["match_name"] for row in rows)),
"top_level":[{k:r[k] for k in ("match_name","grouping","children")} for r in rows if int(r["depth"])==1],
"contents_children":[{k:r[k] for k in ("match_name","display_name","grouping","children")} for r in rows if int(r["depth"])==2 and r["match_name"] in ("ADBE Vector Shape - Rect","ADBE Vector Graphic - Fill")],
"interpretation":"E2-X: AE2026 executed installed fixed AEGP traversal on a native Shape Layer and returned a valid public stream tree. This does not establish new private type registration, original Shape model ABI or custom native rendering.",
"capture_limitations":["Single selected layer: does not compare ordinary footage/effect-only baseline","AEGP public traversal is a projection, not proof of internal ownership or type factory","Effect Parade contains Point Control and Color Control so selected layer is not a minimal empty Shape Layer"]
}
(dst/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("ARCHIVED",dst)
print("SHA",summary["source_sha256"],"ROWS",len(rows),"MAX_DEPTH",summary["max_depth"])
print("GROUPS",summary["group_counts"],"ERRS",summary["error_counts"])
print("TOP",summary["top_level"])
print("CONTENTS",summary["contents_children"])
