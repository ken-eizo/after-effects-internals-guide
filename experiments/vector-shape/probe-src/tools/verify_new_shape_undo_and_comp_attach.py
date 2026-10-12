"""Verify two separate but fundamental native Shape ownership mechanisms:
New Shape Layer command Undo transaction, and genuine type-4 native Shape
construction + CompItem attachment (with layer bookkeeping).
This is machine-code evidence; does NOT prove the entire indirect command-
dispatch edge from BEE_DoCommand to the internal factory.
"""
from pathlib import Path
import json
R=Path(r"D:\Developer\ShapeLayerAE\results")
cmd=json.loads((R/"bee_new_shape_shared_newlayer_worker_2025_2026.json").read_text())["versions"]
creation=json.loads((R/"bee_layer_creation_attach_transaction_contexts_2025_2026.json").read_text())["versions"]
api=json.loads((R/"bee_native_comp_layer_attach_and_new_shape_command_2025_2026.json").read_text())["versions"]
side=json.loads((R/"bee_comp_layer_attach_side_effect_helpers_2025_2026.json").read_text())["versions"]
ref=json.loads((R/"bee_new_shape_command_to_comp_attach_xrefs_2025_2026.json").read_text())["versions"]
out={}
for v in ("2025","2026"):
 core=creation[v]["functions"]["0x3a7ca0" if v=="2025" else "0x3b4110"]
 calls=core["calls"]
 make=[x for x in calls if "CreateLayerFromType@BEE_Layer" in x["export"]]
 attach=[x for x in calls if "AttachLayerToCompOnly@BEE_CompItem" in x["export"]]
 assert len(make)==1 and len(attach)==1
 assert int(make[0]["site"],16)<int(attach[0]["site"],16)
 assert any(x["instr"]=="mov ecx, 4" for x in make[0]["immediate_context"])
 assert any("mov r9b, 1"==x["instr"] for x in attach[0]["immediate_context"])
 assert any("mov r8d" in x["instr"] for x in attach[0]["immediate_context"])
 new=next(z for name,z in api[v]["methods"].items() if name.startswith("?BEE_CmdNewVectorLayer@@"))
 shared=cmd[v]["calls"]
 intro=[x for x in shared if "BEE_StartGroup@@" in x.get("export","")]
 execute=[x for x in shared if "BEE_DoCommand@@" in x.get("export","")]
 end=[x for x in shared if "BEE_EndGroup@@" in x.get("export","")]
 assert len(intro)==len(execute)==len(end)==1
 assert int(intro[0]["at"],16)<int(execute[0]["at"],16)<int(end[0]["at"],16)
 j=[x for x in new["calls"] if x["op"]=="jmp" and x["target"]=="" and
     int(x["args"].split()[-1],16)-0x180000000==int("0x667610" if v=="2025" else "0x682f90",16)]
 assert j,(v,new["calls"])
 owner=next(z for name,z in api[v]["methods"].items() if name.startswith("?AttachLayerToCompOnly@BEE_CompItem@@"))
 param=next(z for name,z in api[v]["methods"].items() if name.startswith("?AttachLayerToCompAndLayerParamsOnly@BEE_CompItem@@"))
 assert len(owner["calls"])==20
 assert len(param["calls"])==2 and "AttachLayerToCompOnly" in param["calls"][0]["target"]
 assert len(side[v]["attach_callees"])==6
 assert side[v]["attach_callees"]["primary_placement"]["byte_count"]>=300
 assert len(ref[v]["create_then_attach"]["verified_x64_instruction_boundary_refs"])>=1
 out[v]={"new_shape_command_export":new["export"],"shared_worker_rva":cmd[v]["function_range"][0],
    "undo_begin_rva":intro[0]["at"],"BEE_DoCommand_rva":execute[0]["at"],"undo_end_rva":end[0]["at"],
    "type4_native_creation_callsite":make[0]["site"],"comp_attachment_callsite":attach[0]["site"],
    "both_calls_in_same_native_function":True,
    "creation_explicit_shape_kind_4":True,
    "comp_attach_uses_position_and_boolean_arguments":True,
    "CompAttach_calculated_direct_calls":len(owner["calls"]),
    "CompAttach_wrapper_then_params_extra_init":True,
    "comp_attach_position_bookkeeper_has_nontrivial_body":True,
    "command_dispatch_to_this_exact_create_function_proven":False,
    "independent_CNL_native_layer_installed":False,
    "private_Adobe_methods_executed":False}
 print("PASS",v,"new vector cmd -> Undo Begin,DoCommand,End; native kind4 factory -> comp attach",flush=True)
dest=R/"bee_new_shape_undo_and_comp_attach_offline_verified_2025_2026.json"
dest.write_text(json.dumps({"status":"cross-version verified native static machine-code structure, NOT an external plugin implementation",
    "versions":out,
    "limits":["DoCommand-to-specific-native-CompItem-factory callback is indirect and not yet resolved",
     "BEE CompItem attach does not prove 3rd party external owner can be accepted",
     "No Adobe runtime loaded or called","No CNL foreign native layer or Pen/Renderer currently exists"]},indent=2)+"\n")
print("SAVED",dest)
