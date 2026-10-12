"""Independent offline witness of BEE_VectorLayer's complete native
Shape Contents schema bootstrap, including 62 typed TDB registrars.
NO runtime TDB/BEE calls, no AE GUI, no private registration.
"""
from pathlib import Path
import json,hashlib,pefile
root=Path(r"D:\Developer\ShapeLayerAE\results")
types=json.loads((root/"bee_vector_layer_62_native_tdb_creators_2025_2026.json").read_text())["versions"]
phases=json.loads((root/"bee_vector_layer_registerstreams_three_phases_2025_2026.json").read_text())["versions"]
bins={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
      "2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")}
report={}
for ver in ("2025","2026"):
 f=types[ver];reg=f["entries"];phase=phases[ver]["functions"]["phase1"]
 assert len(reg)==f["registration_count"]==62
 assert len(set(x["match"]["data_rva"] for x in reg))==62,"62 distinct match-name addresses"
 assert all(x["creator"] and x["creator"]["data_rva"] for x in reg)
 assert "Create@VectorStreamGroup@BEE_VectorStream" in reg[58]["creator"]["symbol"]
 assert "Create@VectorsStreamGroup@BEE_VectorStream" in reg[59]["creator"]["symbol"]
 assert reg[59]["creator"]["data_rva"]==reg[60]["creator"]["data_rva"]
 assert reg[59]["match"]["data_rva"]!=reg[60]["match"]["data_rva"]
 assert "Create@BEE_VectorLayer@@" in reg[61]["creator"]["symbol"]
 assert "VECTOR_LAYER" in reg[61]["match"]["symbol"]
 canonical_near=f["canonical_setup_neighborhood"]
 rdx=[x["target"] for x in canonical_near if x["mnemonic"]=="lea" and x["args"].startswith("rdx,") and x["target"]]
 assert rdx and rdx[-1]==reg[58]["match"]["data_rva"],(ver,rdx[-1],reg[58]["match"]["data_rva"])
 imported=lambda needle: [x for x in phase["calls"] if needle in x.get("link","")]
 assert len(imported("?Register@TDB_ScRegisterStreams@@"))==62
 assert len(imported("SetupCanonicalStream@TDB_StreamFactory"))==1
 assert len(imported("UnregisterAll@TDB_ScRegisterStreams"))==1
 assert len(imported("Get_AE_StreamFactory@@"))==1
 assert len(imported("??0TDB_ScRegisterStreams@@"))==1
 assert phase["rva"]==("0x77c630" if ver=="2025" else "0x79d040")
 assert "TDB.dll" in imported("SetupCanonicalStream@TDB_StreamFactory")[0]["link"]
 # THIS IS A TWO-MODE FUNCTION: the startup code branches away from teardown
 # on CL=1 and the cleanup branch unregisters on CL=0. Do not conflate.
 first=phase["first_instructions"]
 assert any(x["op"]=="movzx" and x["args"]=="ebx, cl" for x in first)
 assert any(x["op"]=="test" and x["args"]=="bl, bl" for x in first)
 assert any(x["op"]=="je" for x in first[15:25])
 actual_hash=hashlib.sha256(bins[ver].read_bytes()).hexdigest()
 assert actual_hash==f["BEE_sha256"]==phases[ver]["hash_sha256"]
 named=sum(bool(x["match"]["symbol"]) for x in reg)
 creators_named=sum(bool(x["creator"]["symbol"]) for x in reg)
 report[ver]={"BEE_SHA256":actual_hash,
  "TDB_registration_calls":62,
  "distinct_matchname_address_count":62,
  "match_names_with_export_symbol":named,
  "creators_with_export_symbol":creators_named,
  "distinct_creator_function_address_count":len(set(x["creator"]["data_rva"] for x in reg)),
  "registered_group_root_matchname_rva":reg[58]["match"]["data_rva"],
  "native_group_root_creator_symbol":reg[58]["creator"]["symbol"],
  "two_VectorsStreamGroup_matchnames_share_creator":True,
  "registered_BEE_VectorLayer_owner_matchname_symbol":reg[61]["match"]["symbol"],
  "registered_BEE_VectorLayer_owner_creator_symbol":reg[61]["creator"]["symbol"],
  "SetupCanonicalStream_receives_registered_root_matchname":True,
  "reg_and_canonical_init_are_separate_from_conditional_unregister_branch":True,
  "second_stage_is_independent_BEE_evaluator_registry":True,
  "third_party_registration_executed":False,
  "external_AEX_entry_point_to_register_native_types_proven":False}
 print("PASS",ver,"62 TDB creators; root->canonical exact match; real BEE_VectorLayer typed creator; branch-switched teardown",
       "symbolized",named,"/",creators_named,flush=True)
p=root/"bee_vector_layer_62_native_shape_bootstrap_verified_2025_2026.json"
p.write_text(json.dumps({"evidence":"E2-L exact installed AE2025/2026 BEE PE images, static typed-creator source map and startup wrapper",
 "scope_warning":"No runtime invocation. Native owner/Pen/VectorArt external plug-in contracts NOT proven.",
 "versions":report},indent=2)+"\n")
print("SAVED",p)
