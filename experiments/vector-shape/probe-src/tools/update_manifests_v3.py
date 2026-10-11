"""Reconcile EXP-SHAPE-005 manifest with preserved actual user-executed v2 host evidence.
Do not alter unrelated AEIG files.
"""
from pathlib import Path
import json
root=Path(r"D:\Developer\After Effects Internals Guide")
p=root/r"experiments\observatory\manifests\EXP-SHAPE-005.json"
j=json.loads(p.read_text(encoding="utf-8"))
j["status"]="observed-v2-in-host; v3-compiled-pending-host"
j["conclusion"]="E2-X AE2026 v2 host capture: 359 valid public stream records, 36 successful built-in child CanAdd decisions, 359 GetUniqueStreamID calls returned zero without API error; v3 sentinel and unknown-name probes remain compiled-only."
j["observed_host_capture"]={
 "date_local":"2026-10-11T18:45:17",
 "files":"experiments/vector-shape/runs/EXP-SHAPE-005/20261011-user-host-v2",
 "tree_sha256":"38243e05de1d447d8b71104c4d73f4ddd01d778b627d6abceaf14db0ff9b5432",
 "metadata_sha256":"ba1e318ca21c8a893933b14517a92be46b0ae45c65373cea5089495b7a56767d",
 "canadd_sha256":"8b51d257014bebcfdc9a7ee1ae348d43d863e408244b6bf026d584c61a40fba0",
 "stream_count":359,"canadd_query_count":36,"stream_id_zero_count":359,"nonzero_error_count":0,
 "report":"experiments/vector-shape/EXP-SHAPE-005-v2-host-confirmation.md"}
p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
for e in ("EXP-SHAPE-009","EXP-SHAPE-010"):
    q=root/"experiments"/"observatory"/"manifests"/(e+".json")
    m=json.loads(q.read_text(encoding="utf-8"))
    m["build_receipt"]={"binary":"D:/Developer/ShapeLayerAE/build/Release/ShapeLayerAE.aex",
        "sha256":"6a20aaa59100a68aaa5e8aa4af126756a9dd8dd6cf50951dce8cf1bf6ec6dbf1",
        "installed_version":"older v2; current user AE process not touched",
        "host_result":"pending"}
    q.write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("MANIFESTS reconciled and pinned")
