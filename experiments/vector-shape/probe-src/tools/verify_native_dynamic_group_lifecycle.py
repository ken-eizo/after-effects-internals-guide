"""Cross-check concrete native dynamic group generation and temporary registration
with real AE2026 public AEGP group-admission observation.
All host binary observations static; does not call private APIs.
"""
from pathlib import Path
import json
base=Path(r"D:\Developer\ShapeLayerAE\results")
def load(s):return json.loads((base/s).read_text(encoding="utf-8"))
rtti=load("bee_dynamic_parser_derived_RTTI_vtable_scan_2025_2026.json")["years"]
vtable=load("bee_dynamic_effect_creator_gate_vtable_2025_2026.json")["versions"]
instance=load("bee_layer_style_parser_real_group_verified_2025_2026.json")["versions"]
callers=load("bee_layer_style_parser_creation_callers_2025_2026.json")["versions"]
factory=load("tdb_scoped_registry_lifetime_abi_2025_2026.json")["versions"]
host=load("ae2026_owner_admission_host_aggregate_20261012.json")
assert host["visited_nodes"]==186 and host["tested_groups"]==33
assert host["cnl_matchname_negative_admissions"]==33
assert host["private_registry_invoked"] is False
proof={}
for ver in ("2025","2026"):
 classes=rtti[ver]["validated_rtti_vtables"]
 assert len(classes)==2,(ver,classes)
 derived=next(c for c in classes if "LayerStyleStreamGroupParser" in c["type"])
 nativebase=next(c for c in classes if "DynamicStreamEffectsParser" in c["type"])
 assert nativebase["virtual_slot22_target_rva"]==vtable[ver]["sites"]["0xb0"]["rva"]
 assert derived["virtual_slot22_target_rva"]==instance[ver]["override_rva"]
 assert instance[ver]["returns_concrete_group"]
 routine=max(callers[ver]["routines"],key=lambda r:len(r["edges"]))
 edges=routine["edges"]
 def matching(term):
  return [e for e in edges if term in e.get("symbol","")]
 n_reg=len(matching("?Register@TDB_ScRegisterStreams@@"))
 n_layout=len(matching("?AddStreamToUILayout@TDB_StreamGroup@@"))
 n_parser=len(matching("?GetParser@xml@dvacore@@"))
 n_unreg=len(matching("?UnregisterAll@TDB_ScRegisterStreams@@"))
 assert (n_reg,n_layout,n_parser,n_unreg)==(11,2,1,1),(ver,n_reg,n_layout,n_parser,n_unreg)
 assert any("UnregisterFactoryFunc@TDB_StreamFactory@@" in e.get("symbol","") for e in factory[ver]["methods"]["unregister_all"]["edges"])
 count_extra=len(matching("?UnregisterFactoryFunc@TDB_StreamFactory@@"))
 assert count_extra==(1 if ver=="2025" else 0)
 proof[ver]={"two_native_rtti_descendants":True,
             "genuine_derived_group_creator":derived["virtual_slot22_target_rva"],
             "created_native_type":"IndLayerStyleStreamGroup",
             "object_size":instance[ver]["object_allocation_size"],
             "native_scoped_register_calls":n_reg,
             "native_add_child_layout_calls":n_layout,
             "native_xml_parser_acquisition_calls":n_parser,
             "explicit_scoped_unregister_all_calls":n_unreg,
             "additional_direct_factory_unregister_calls":count_extra,
             "scoped_unregister_all_imports_factory_unregister":True,
             "third_party_independent_contents_created":False,
             "native_pen_or_vector_renderer_integrated":False}
 print("PASS",ver,"11 register / 2 AddUILayout / 1 XML parser / 1 explicit scoped unregister",flush=True)
dest=base/"native_dynamic_vector_group_lifecycle_crosscheck_2025_2026.json"
dest.write_text(json.dumps({"classification":"E2-L cross-version BEE/TDB native compiled code, E2-X bounded public owner scan",
"host_2026_public_readonly":{"visited_nodes":186,"parent_groups":33,"CNL_rejected":33},
"versions":proof,"limitations":["host 2026 scan on existing Shape Layer, not CNL plugin",
 "no private type registration or parser execution","CNL renderer and editor gates remain open"]},indent=2)+"\n")
print("SAVED",dest)
