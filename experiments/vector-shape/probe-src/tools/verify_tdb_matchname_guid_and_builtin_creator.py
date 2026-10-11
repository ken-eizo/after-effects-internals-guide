"""EXP-SHAPE-029 (static): bounded native MatchName GUID and complete
Adobe ParamPathStream Creator as a candidate for *disposable* registration.

This verifier never invokes any Adobe native function; no AE/UI operations.
"""
from pathlib import Path
import json
import hashlib
root=Path(r"D:\Developer\After Effects Internals Guide\datasets")
candidate=json.loads((root/"ae-native-tdb-built-in-path-creator-registration-feasibility-2025-2026.json").read_text("utf8"))
factory=json.loads((root/"ae-native-stream-private-registration-lifetime-2025-2026.json").read_text("utf8"))
out={}
for yr in ("2025","2026"):
 c=candidate["versions"][yr]
 f=c["functions"]
 method=f["matchname_from_chars"]
 ops=method["first30_instructions"]
 assert any(x["opcode"]=="vmovups" and x["operands"]=="xmmword ptr [rdi], xmm0" for x in ops),yr
 assert any("GuidFromName@TDBp_MatchNamePool@@" in call["symbol"] for call in method["symbolized_calls"]),yr
 path=f["native_path_create"]
 pop=path["first30_instructions"]
 assert any(i["opcode"]=="mov" and i["operands"]=="ecx, 0x468" for i in pop),yr
 assert any("U_MemTrackedObject" in x["symbol"] for x in path["symbolized_calls"]),yr
 assert any("TDB_DerivedStream@UTDB_ParamPathStreamTraits" in x["symbol"] for x in path["symbolized_calls"]),yr
 ctor=f["native_indexed_group_ctor"]
 assert any("??0TDB_StreamGroup@@" in x["symbol"] for x in ctor["symbolized_calls"]),yr
 reg=factory["versions"][yr]
 assert reg["registration_eager_CreateStream_sites"]
 assert not reg["third_party_abi_safe"]
 out[yr]={
  "source_tdb_sha256":c["TDB_sha256"],
  "MatchName_char_ctor_rva":f["matchname_from_chars"]["entry_rva"],
  "MatchName_internal_payload_static_observation":"16-byte GUID copied from TDBp_MatchNamePool::GuidFromName",
  "MatchName_cpp_class_layout_fully_known":False,
  "ParamPathStream_create_rva":path["entry_rva"],
  "ParamPathStream_create_allocation_bytes":0x468,
  "ParamPathStream_derived_traits":"TDB_ParamPathStreamTraits",
  "ParamPathStream_is_native_BEE_VectorArt":False,
  "ParamPathStream_can_be_assigned_new_external_matchname_proven":False,
  "independent_parent_timeline_owner_proven":False,
  "static_candidate_for_host_test":True
 }
 print("PASS",yr,"MatchName 16-byte GUID write; complete ParamPathStream native allocator 0x468; still NOT native external registration")
file=root/"ae-tdb-matchname-guid-and-built-in-path-creator-check-2025-2026.json"
file.write_text(json.dumps({"classification":"E2-L native symbol+first30 x64 assembly cross-check only",
 "hypothesis":"an existing complete ParamPathStream creator might be used as a safer host-registry acceptance test",
 "warning":"C++ MatchName class layout, callback value ABI, host lifetime and native editor ownership are still unverified",
 "versions":out},indent=2)+"\n",encoding="utf8")
print("SAVED",file)
