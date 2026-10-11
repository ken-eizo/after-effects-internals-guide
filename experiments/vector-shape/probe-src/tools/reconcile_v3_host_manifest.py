from pathlib import Path
import json
r=Path(r"D:\Developer\After Effects Internals Guide")
d=r/"experiments/observatory/manifests"
for x in ("EXP-SHAPE-009","EXP-SHAPE-010"):
    p=d/(x+".json")
    obj=json.loads(p.read_text(encoding="utf-8"))
    obj["status"]="observed-in-host"
    obj["host_result"]={
        "date_local":"2026-10-11",
        "host":"AE2026",
        "installed_aex_sha256":"6a20aaa59100a68aaa5e8aa4af126756a9dd8dd6cf50951dce8cf1bf6ec6dbf1",
        "report":"experiments/vector-shape/EXP-SHAPE-009-010-v3-host-confirmation.md",
        "archive":"experiments/vector-shape/runs/EXP-SHAPE-009-010/20261011-user-host-v3",
    }
    if x=="EXP-SHAPE-009":
        obj["host_result"].update({"unknown_matchname_canadd_queries":72,
            "errors":0,"streams_with_two_uid_calls":359,"uid_nonzero_count":0})
        obj["conclusion"]="E2-X host: unknown Shape/Graphic/Filter prefixed match names are admitted into existing native Contents by CanAdd without being created; 359x2 UID calls returned zero/error0."
    else:
        obj["host_result"].update({"getter_module_found":True,"getter_export_present":True,
            "fingerprint_ok":True,"factory_return_nonnull":True,"private_method_calls_other_than_getter":0})
        obj["conclusion"]="E2-X host: independently installed AEGP resolves and calls the private no-argument getter and obtains a nonnull factory pointer. No dereference, registration or mutation."
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
p=d/"EXP-SHAPE-005.json"
obj=json.loads(p.read_text(encoding="utf-8"))
obj["v3_uid_followup"]={"raw_path":"experiments/vector-shape/runs/EXP-SHAPE-009-010/20261011-user-host-v3/ShapeLayerAE_stream_metadata.tsv","streams":359,"two_calls_per_stream":True,"both_errors_zero":True,"both_uid_zero":True}
p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
for id,title,question,results in [
("EXP-SHAPE-011","Native Shape typed creator registration bundle reverse engineering",
"Do actual built-in BEE_VectorStream Creator callbacks feed into the native TDB_ScRegisterStreams::Register?",
"4 true Windows x64 function regions per version, 31 explicit creator-address references; 183 TDB Register direct IAT callsites per version."),
("EXP-SHAPE-012","VectorLayer native evaluated VectorArt handoff",
"Does BEE_VectorLayer::GetVectorArt invoke TDB stream path creation and PopulateVectorArt before bounds?",
"Both versions have direct CALLs to Group constructor, TDB_StreamID, TDB_StreamIDPath, PopulateVectorArt, GetBounds; path returns intrusive VectorArt group.")
]:
    x={"experiment_id":id,"title":title,"status":"observed-static-only",
       "question":question,"evidence":["E2-L"],
       "environment":{"installed_binaries":"AE 2025/2026","host_private_mutations":False},
       "observed_result":results,
       "limitations":["Offline CALL references do not prove native third-party custom type registration","No native independent CompNodeAE-owned vector object has been created"]}
    (d/(id+".json")).write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Updated manifest statuses: v3 host E2-X; v2 follow-up; 011/012 static.")
