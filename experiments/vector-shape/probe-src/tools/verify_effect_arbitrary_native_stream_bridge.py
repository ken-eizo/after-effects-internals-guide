"""Offline binary proof: Adobe FLT's native TDB-derived stream backs
PF_Param_ARBITRARY_DATA. This is an existing host leaf, not a CNL group.
"""
import json
from pathlib import Path
base=Path(r"D:\Developer\ShapeLayerAE\results")
corpus=json.loads((base/"flt_effect_arbitrary_tdb_stream_bridge_2025_2026.json").read_text())["versions"]
out={}
for v in ("2025","2026"):
 d=corpus[v];m=d["methods"]
 def exported(key,part):
  assert part in m[key]["export"],(v,key,part)
 def target(key,part):
  return [x for x in m[key]["edges"] if part in x["callee"]]
 exported("arb_create","FLT_ParamArbDataStream")
 exported("arb_clone","FLT_ParamArbDataStream")
 exported("seq_param_stream","FLT_SeqInqParamStream")
 assert "FLT_ParamArbDataStream" in d["arbitrary_vtable"][0]
 for k in ("arb_create","arb_clone"):
  ins=m[k]["instructions"]
  assert any(x["op"]=="mov" and x["args"]=="ecx, 0x470" for x in ins),(v,k)
 assert target("arb_create","??0FLT_ParamArbDataStream@@")
 assert target("arb_clone","??0FLT_ParamArbDataStream@@")
 assert target("arb_ctor","TDB_DerivedStream@UFLT_ParamArbDataStreamTraits")
 assert target("arb_dispose","DeleteArbDataItem@FLT_ParamArbDataStream")
 assert target("arb_delete","GetParamDef@TDB_StreamBase")
 assert target("arb_delete","GetValueDesc@TDB_Stream")
 for operation in ("arb_print","arb_print_size","arb_scan"):
  assert target(operation,"GetAssociatedArbDataEffect_Impl"),(v,operation)
 assert target("arb_scan","U_UTF16ToMBString")
 assert target("arb_scan","U_MBToUTF16String")
 out[v]={"FLT_sha256":d["sha256"],
 "native_param_type":"FLT_ParamArbDataStream inherits TDB_DerivedStream<FLT_ParamArbDataStreamTraits>",
 "actual_cpp_vtable":d["arbitrary_vtable"],
 "allocation_bytes":0x470,
 "factory_creator_rva":m["arb_create"]["start"],
 "clone_rva":m["arb_clone"]["start"],
 "sequence_effect_param_to_native_stream_lookup_rva":m["seq_param_stream"]["start"],
 "host_native_dispose_uses_effect_paramdef":True,
 "host_native_print_scan_reach_associated_effect":True,
 "CNL_separate_native_TDB_registration_proven":False,
 "native_pen_gizmo_targets_arbitrary_stream":False}
 print("PASS",v,"native FLT arbitrary leaf, ctor/clone, typed disposal, effect-bound print/scan")
target=base/"flt_effect_arbitrary_native_stream_verified_2025_2026.json"
target.write_text(json.dumps({"scope":"E2-L pinned AE2025/26 FLT PE. No Adobe methods invoked.",
 "versions":out,"limitations":["No actual host test of new AEX",
 "Real FLT_ParamArbDataStream is an Adobe-native wrapper of data, not independently registered CNL Vector Contents",
 "Native Pen hit testing and BEE_VectorArt remain unproven"]},indent=2)+"\n")
print("SAVED",target)
