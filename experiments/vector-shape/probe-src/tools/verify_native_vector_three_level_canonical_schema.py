"""Verify the real 3-level Adobe native Shape/Contents schema across AE2025/26
using actual BEE exported virtual methods and the 183 TDB typed factory calls.
Only verified native bytecode links; no host mutation.
"""
import json,hashlib
from pathlib import Path
base=Path(r"D:\Developer\ShapeLayerAE\results")
schema=json.loads((base/"bee_vector_native_layer_contents_allowed_children_2025_2026.json").read_text())["versions"]
registries=json.loads((base/"bee_native_vector_all183_tdb_registration_pipeline_2025_2026.json").read_text())["versions"]
typereg=json.loads((base/"bee_vector_layer_62_native_tdb_creators_2025_2026.json").read_text())["versions"]
evaluator=json.loads(Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-vector-evaluator-matchname-identities-2025-2026.json").read_text())["versions"]
report={}
names={}
for version in ("2025","2026"):
 root,group,contents=schema[version]["three_schema_classes"]
 assert "BEE_VectorLayer" in root["symbol"]
 assert "VectorStreamGroup" in group["symbol"]
 assert "VectorsStreamGroup" in contents["symbol"]
 assert [root["canonical_child_lookup_count"],group["canonical_child_lookup_count"],contents["canonical_child_lookup_count"]]==([10,4,20] if version=="2025" else [11,4,20])
 arr=lambda obj:[item["last_matchname_arg"]["matchname_rva"] for item in obj["canonical_children"]]
 layer,grp,cts=arr(root),arr(group),arr(contents)
 typed={r["match"]["data_rva"]:r for r in typereg[version]["entries"]}
 keymap={r["matchname_global_rva"]:r["name"] for r in evaluator[version]["records"]}
 named=[keymap.get(r) for r in cts]
 assert all(named) and len(set(named))==20
 assert cts[0]==typereg[version]["entries"][58]["match"]["data_rva"]
 assert cts[0] in keymap and keymap[cts[0]]=="ADBE Vector Group"
 assert grp[1]==typereg[version]["entries"][59]["match"]["data_rva"]
 assert grp[2]==typereg[version]["entries"][56]["match"]["data_rva"]
 assert grp[3]==typereg[version]["entries"][48]["match"]["data_rva"]
 assert layer[1]==typereg[version]["entries"][60]["match"]["data_rva"]
 assert len(layer)==len(set(layer)) and len(grp)==len(set(grp)) and len(cts)==len(set(cts))
 assert len(registries[version]["operator_matchnames_joined_to_native_TDB_creator_registration"])==20
 assert registries[version]["total_static_registration_calls"]==183
 # all 20 operator keys in the canonical contents must have an actual TDB typed factory registration
 for name in named:
  assert name in registries[version]["operator_matchnames_joined_to_native_TDB_creator_registration"],(version,name)
 assert sum(name.startswith("ADBE Vector Shape -") for name in named)==4
 assert sum(name.startswith("ADBE Vector Graphic -") for name in named)==4
 assert sum(name.startswith("ADBE Vector Filter -") for name in named)==11
 assert named[0]=="ADBE Vector Group"
 names[version]=named
 report[version]={"BEE_SHA256":schema[version]["BEE_SHA256"],
  "layer_canonical_slots":len(layer),"vector_stream_group_fixed_canonical_slots":len(grp),
  "contents_child_type_count":len(cts),"shape_type_count":4,"graphic_type_count":4,"filter_type_count":11,
  "contents_canonical_types_in_native_order":named,
  "vector_stream_group_canonical_ref_registrations":{
    "contents_group_slot_1":"VectorsStreamGroup::Create (entry 59)",
    "transform_group_slot_2":"TransformStreamGroup::Create (entry 56)",
    "3d_material_options_group_slot_3":"Vec3D_MaterialOptionsStreamGroup::Create (entry 48)",
    "slot_0":"native group canonical child exists; no matching direct registration in 62-entry block"},
  "layer_canonical_child_belonging_to_VectorsStreamGroup_registry_entry_60":True,
  "TDB_creator_site_count":183,
  "all_twenty_contents_child_types_have_creator_registrations":True,
  "user_CNL_content_type_registered":False,
  "independent_plugin_vector_layer_enabled":False}
 print("PASS",version,"Layer",len(layer),"VectorGroup",len(grp),"Contents",len(cts),
       "20/20 TDB creator links",flush=True)
assert names["2025"]==names["2026"],"native Contents user-visible ordering changed across pinned builds"
out=base/"bee_native_vector_three_level_canonical_schema_cross_verified_2025_2026.json"
out.write_text(json.dumps({"evidence":"E2-L actual exported BEE native 3-level FillInCanonicalUILayout implementations, all 183 typed registration call sites, 20 operator typed creators","versions":report,
 "across_two_versions_all_twenty_contents_types_same_order":True,
 "limitations":["Native schema not yet externally injectable","No foreign class instance","No native Pen/Undo/RG acceptance demonstrated","No private host function invoked"]},ensure_ascii=False,indent=2)+"\n")
print("SAVED",out)
