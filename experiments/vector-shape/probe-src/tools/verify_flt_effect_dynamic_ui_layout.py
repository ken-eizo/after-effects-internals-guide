"""Cross-check FLT_FCSeqSpec nested dynamic group layout production.
E2-L exact compiled native PE, no host execution.
"""
import json
from pathlib import Path
root=Path(r"D:\Developer\ShapeLayerAE\results")
a=json.loads((root/"flt_effect_canonical_layout_builder_2025_2026.json").read_text())["versions"]
b=json.loads((root/"flt_fcseqspec_nested_canstore_tdb_2025_2026.json").read_text())["versions"]
c=json.loads((root/"tdb_group_canstore_canonical_whitelist_2025_2026.json").read_text())["versions"]
out={}
for y in ("2025","2026"):
 fs=a[y]["functions"]
 def find(prefix):
  xs=[z for z in fs if z["symbol"].startswith(prefix)]
  assert len(xs)==1,(y,prefix,len(xs))
  return xs[0]
 initial=find("?FillInCanonicalUILayout@FLT_FCSeqSpec@@")
 assert initial["prologue"][0]["mnemonic"]=="ret",(y,initial["prologue"][:4])
 assert not initial["calls"],(y,initial["calls"])
 add=find("?AddStreamToUILayout@FLT_FCSeqSpec@@")
 assert any("GetUILayout@TDB_StreamGroup@@" in q["name"] for q in add["calls"])
 assert b[y]["inherited_canstore_import"].startswith("TDB.dll!?CanStore@TDB_StreamGroup@@")
 assert c[y]["exact_matchname_comparison"]
 out[y]={"flt_sha256":b[y]["flt_sha256"],"tdb_sha256":b[y]["tdb_sha256"],
 "empty_default_canonical_UI_fill":True,
 "add_stream_uses_generic_TDB_GetUILayout":True,
 "nested_canstore_uses_TDB_matchname_whitelist":True,
 "actual_dynamic_plugin_vector_owner_proven":False}
 print("PASS",y,"empty FillInCanonicalUILayout + runtime AppendToUILayout + TDB allowed-name match")
p=root/"flt_effect_nested_dynamic_group_layout_verified_2025_2026.json"
p.write_text(json.dumps({"classification":"E2-L caller semantics not fully traced","versions":out},indent=2)+"\n")
print("SAVED",p)
