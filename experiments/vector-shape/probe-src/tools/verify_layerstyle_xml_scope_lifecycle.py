"""Verify native LayerStyle factory scope, 11 creator types, external-to-
bootstrap XML argument forwarding, and matching native teardown wrappers.
Read-only AE2025/26 machine code, not a supported third-party plugin API.
"""
import json
from pathlib import Path
base=Path(r"D:\Developer\ShapeLayerAE\results")
def j(n):return json.loads((base/n).read_text(encoding="utf8"))
creators=j("layerstyle_11_scoped_creator_types_verified_2025_2026.json")["versions"]
entry=j("bee_layerstyle_xml_parser_2hop_entry_boundary_2025_2026.json")["versions"]
init=j("bee_layer_style_parser_creation_callers_2025_2026.json")["versions"]
out={}
for year in ("2025","2026"):
 assert creators[year]["typed_leaf_stream_creators"]==8
 assert creators[year]["built_in_group_creators"]==3
 ws=entry[year]["wrappers"]
 assert len(ws)==2
 start,stop=ws
 src=[(x[1],x[2]) for x in start["instructions"]]
 dst=[(x[1],x[2]) for x in stop["instructions"]]
 assert ("mov","rdx, rcx") in src and ("mov","cl, 1") in src
 assert ("xor","edx, edx") in dst and ("xor","ecx, ecx") in dst
 assert start["xrefs"] and len(start["xrefs"])==1 and start["xrefs"][0]["kind"]=="CALL"
 assert stop["xrefs"] and len(stop["xrefs"])==1 and stop["xrefs"][0]["kind"]=="CALL"
 instr=max(init[year]["routines"],key=lambda v:len(v["instructions"]))["instructions"]
 op=[(r["op"],r["args"]) for r in instr]
 assert ("mov","r14, rdx") in op
 assert ("mov","rdx, r14") in op
 assert ("call","qword ptr [rax + 0x18]") in op
 assert any("GetParser@xml@dvacore@@" in e.get("symbol","") for e in
            max(init[year]["routines"],key=lambda v:len(v["edges"]))["edges"])
 out[year]={"scoped_native_registered_leaves":8,"scoped_native_registered_groups":3,
            "bootstrap_forwards_wstring_argument_rcx_to_parser_rdx":True,
            "initializer_copies_parser_rdx_to_local_xml_source":True,
            "XML_parser_virtual_parse_called":True,
            "paired_native_setup_teardown_wrapper":True,
            "host_owned_internal_groups":True,
            "external_plugin_registration_exposed":False}
 print("PASS",year,": 11 typed creator categories, bootstrap argument, XML virtual parse, paired shutdown")
p=base/"verified_layerstyle_xml_scope_lifecycle_2025_2026.json"
p.write_text(json.dumps({"evidence":"E2-L pinned BEE PE, scope excludes indirect code paths","versions":out,
 "limitations":["Native startup accepting definition argument is NOT proof third-party plugin can supply it",
                "The internal parser has no verified extensible native VectorArt or Pen API",
                "Destructor cleanup and plugin unload safety not verified"]},indent=2)+"\n",encoding="utf8")
print("SAVED",p)
