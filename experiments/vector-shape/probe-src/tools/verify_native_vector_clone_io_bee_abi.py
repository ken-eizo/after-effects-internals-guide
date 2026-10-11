"""Crossvalidate native TDB clone, serialization and BEE evaluator-ownership gates.

E2-L from installed binaries, JSON receipts created by independent disassemblers.
Records compact facts, NOT a claim that an external Effect SDK effect can use
native TDB or VectorArt. Safe to run with After Effects open.
"""
import json
from pathlib import Path
root=Path(r"D:\Developer\After Effects Internals Guide\datasets")
tdb=json.loads((root/"ae-tdb-native-clone-serialization-parent-callgraph-2025-2026.json").read_text(encoding="utf-8"))
bee=json.loads((root/"ae-bee-evaluator-register-shutdown-callback-abi-2025-2026.json").read_text(encoding="utf-8"))
def hits(records,needle):
 return [r for r in records if needle in r.get("resolved","")]
out={}
for year in ("2025","2026"):
 methods=tdb["versions"][year]["methods"]
 native=bee["versions"][year]["code"]
 assert methods["clone_base"]["indirect_virtual_calls"][0]["byte_offset"]=="0x8"
 assert hits(methods["clone_leaf"]["resolved_calls"],"??0TDB_Stream@@")
 assert hits(methods["clone_parampath"]["resolved_calls"],"TDB_DynamicEnglishDisplayNameNonLeaf")
 assert hits(methods["read_group"]["resolved_calls"],"ReadUniqueStreamID@TDB_StreamBase")
 assert hits(methods["read_group"]["resolved_calls"],"Read@TDB_MatchName")
 assert hits(methods["write_group"]["resolved_calls"],"WriteUniqueStreamID@TDB_StreamBase")
 assert hits(methods["write_group"]["resolved_calls"],"Write@TDB_MatchName")
 assert hits(methods["write_group"]["resolved_calls"],"GetCanonicalStream@TDB_StreamFactory")
 assert hits(methods["write_group"]["resolved_calls"],"WriteEndOfGroupMarker")
 assert hits(methods["read_leaf"]["resolved_calls"],"ReadUniqueStreamID@TDB_StreamBase")
 assert hits(methods["write_leaf"]["resolved_calls"],"WriteUniqueStreamID@TDB_StreamBase")
 assert hits(methods["write_leaf"]["resolved_calls"],"GetExpression@TDB_Stream")
 assert hits(methods["write_leaf"]["resolved_calls"],"GetKeyData@TDB_Stream")
 assert hits(methods["write_leaf"]["resolved_calls"],"HasKeys@TDB_Stream")
 assert hits(methods["write_leaf"]["resolved_calls"],"SLU_WriteAtom")
 assert hits(methods["read_leaf"]["resolved_calls"],"SLU_ReadAtom")
 assert hits(methods["canonical_layout"]["resolved_calls"],"SetUILayout@TDB_StreamGroup")
 assert hits(methods["parent_base"]["resolved_calls"],"NotifyParentsStreamStored")
 assert hits(methods["parent_base"]["resolved_calls"],"TDB_RescaleStream")
 assert native["reg"]["virtual_calls"] and any(c["disp"]=="0x8" for c in native["reg"]["virtual_calls"])
 assert len(native["reg"]["calls"])>=15
 assert not any("Unregister" in c.get("target","") for c in native["reg"]["calls"])
 reg_symbols= [c["target"] for c in native["reg"]["calls"]]
 assert any("TDB_MatchName" in s for s in reg_symbols)
 assert native["lookup"]["calls"]
 assert native["accessor"]["references_to_global_data"]
 out[year]={
 "stream_clone_base_dispatch":{"slot":"0x8","verified":True},
 "clone_leaf_class_ctor":True,
 "clone_path_stream_derived_class_ctor":True,
 "group_read_handles_native_matchname_and_unique_id":True,
 "group_write_checks_canonical_and_writes_matchname_id_and_end_marker":True,
 "leaf_read_native_id_and_values":True,
 "leaf_write_native_id_key_data_expressions":True,
 "canonical_UI_layout_created_by_stream_group":True,
 "parent_set_notifies_owning_group":True,
 "BEE_separate_matchname_operator_registrar_and_lookup":True,
 "BEE_registry_global_accessor":True,
 "BEE_registrar_addref_release_style_virtual_calls":{
  "disps":[r["disp"] for r in native["reg"]["virtual_calls"]],
  "assumption":"likely refcounting; exact vtable method names not recovered"},
 "existing_AE_native_serialization_supported":True,
 "new_plugin_stream_registered":False,
 "independent_contents_and_native_raster":False
 }
 print("PASS",year, "native TDB stream clone/ID/IO/parent/UILayout and BEE evaluator registration verified offline")
dest=root/"ae-native-vector-owner-serialization-gates-2025-2026.json"
dest.write_text(json.dumps({
 "classification":"E2-L independent callgraph consistency; not public SDK or live plugin behavior",
 "result":"AE native object ownership and serialization have multiple type-specific callback dependencies",
 "versions":out},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dest)
