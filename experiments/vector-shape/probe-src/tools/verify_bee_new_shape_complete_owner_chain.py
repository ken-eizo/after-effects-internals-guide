"""Native Shape creation COMPLETE static chain proof across installed AE2025/26:
CmdNewVectorLayer -> Undo worker -> BEE_DoCommand 32-byte table ->
+8 callback constructs BEE_NewLayerTask<4> -> MSVC virtual slot1 ->
new layer worker -> real stock native CreateLayerFromType -> CompItem Attach.

E2-L native PE only. Does not prove foreign CNL native owner ABI.
"""
from pathlib import Path
import json, re,hashlib
root=Path(r"D:\Developer\ShapeLayerAE\results")
def dataset(name):return json.loads((root/name).read_text())["versions"]
api=dataset("bee_native_comp_layer_attach_and_new_shape_command_2025_2026.json")
table=dataset("bee_native_command_table_32byte_entries_2025_2026.json")
handler=dataset("bee_new_shape_exact_command_table_handlers_2025_2026.json")
rtti=dataset("bee_new_shape_command_object_rtti_vtable_2025_2026.json")
virtual=dataset("bee_newshape_task4_vtable_virtual_calltargets_2025_2026.json")
work=dataset("bee_real_newlayer_task4_factory_worker_2025_2026.json")
attach=dataset("bee_newtask4_creation_to_comp_attach_reachability_2025_2026.json")
owner=dataset("bee_vector_owner_factory_vs_generic_layer_dispatch_2025_2026.json")
command=dataset("bee_new_shape_undo_and_comp_attach_offline_verified_2025_2026.json")
bins={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
"2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
codes={"2025":101,"2026":106};proof={}
for v in ("2025","2026"):
 ident=codes[v]
 c=next(x for k,x in api[v]["methods"].items() if k.startswith("?BEE_CmdNewVectorLayer"))
 first=[x["op"]+" "+x["args"] for x in c["instructions"][:5]]
 assert "mov edx, "+hex(ident) in first
 assert "mov r8d, 0x306" in first
 command_entry=table[v]["entries"][ident]
 assert command_entry["entry_rva"]==handler[v]["record_rva"]
 e8=handler[v]["callback_factory_plus8"];e16=handler[v]["callback_execution_plus16"]
 assert command_entry["pointers_rva"][1]==e8["rva"]
 assert command_entry["pointers_rva"][2]==e16["rva"]
 assert any(x["op"]=="mov r8d, 4" for x in e8["instructions"])
 def resolve_vftable(callback):
  ins=callback["instructions"]
  store=next(i for i,x in enumerate(ins) if x["op"]=="mov qword ptr [rbx], rax")
  target=ins[store-1]
  match=re.fullmatch(r"lea rax, \[rip \+ (0x[0-9a-f]+)\]",target["op"])
  assert match,target
  return hex(int(target["site"],16)+7+int(match.group(1),16))
 assert resolve_vftable(e8)==rtti[v]["vtable_rva"]
 assert resolve_vftable(e16)==rtti[v]["vtable_rva"]
 assert rtti[v]["RTTI_Cpp_class_decorated"]==".?AV?$BEE_NewLayerTask@$03@@"
 assert len(rtti[v]["virtual_methods"])==3
 slot1=rtti[v]["virtual_methods"][1]["function_rva"]
 assert virtual[v]["virtuals"][1]["entry_rva"]==slot1
 worker=work[v]["entry_rva"]
 assert any(x.get("target_rva")==worker for x in virtual[v]["virtuals"][1]["calls"])
 factory=[x for x in work[v]["calls"] if "CreateLayerFromType@BEE_Layer" in x.get("symbol","")]
 assert len(factory)==1,factory
 stock_creator=next(x for k,x in owner[v]["factories"].items() if k.startswith("?CreateLayerFromType@"))
 assert factory[0]["to_rva"]==stock_creator["entry_rva"]
 comp=[x for x in work[v]["calls"] if "BEE_SetLayerPositionFromCompOffset" in x.get("symbol","")]
 assert len(comp)==1
 assert any("TDB_StreamIDPath" in x.get("symbol","") for x in work[v]["calls"])
 assert any("BEE_CmdSeparateStreamDimensions" in x.get("symbol","") for x in work[v]["calls"])
 path=attach[v]["discovered_direct_path"]
 assert path and path["node_path"][0]==worker
 target_attach=next(x for k,x in api[v]["methods"].items() if k.startswith("?AttachLayerToCompOnly@"))
 assert path["node_path"][-1]==target_attach["entry_rva"]
 assert command[v]["undo_begin_rva"] and command[v]["undo_end_rva"]
 filehash=hashlib.sha256(Path(bins[v]).read_bytes()).hexdigest()
 assert filehash==rtti[v]["sha256"]==api[v]["BEE_sha256"]
 proof[v]={
  "native_BEE_hash_sha256":filehash,
  "NewVectorLayer_command_id":ident,
  "Undo_Begin_DoCommand_End_proven":True,
  "table_entry_rva":command_entry["entry_rva"],
  "constructor_callback_plus8":e8["rva"],
  "alternate_constructor_callback_plus16":e16["rva"],
  "both_callbacks_construct_same_rtti_type":True,
  "RTTI_Cpp_class":rtti[v]["RTTI_Cpp_class_decorated"],
  "type_4_set_in_task_constructor":True,
  "vtable_rva":rtti[v]["vtable_rva"],
  "task_virtual_slot1_rva":slot1,
  "task_virtual_native_worker":worker,
  "worker_calls_BEE_Layer_CreateLayerFromType_at":factory[0]["rva"],
  "worker_calls_BEE_SetLayerPositionFromCompOffset_at":comp[0]["rva"],
  "worker_uses_real_TDB_StreamIDPath":True,
  "worker_to_native_CompItemAttach_real_direct_sites":path["call_sites"],
  "worker_to_native_CompItemAttach_route":path["node_path"],
  "static_code_chain_complete":True,
  "runtime_foreign_layer_type_registered":False,
  "ABI_safe_from_AEX":False,
  "native_Pen_BEE_VectorArt_CNL_connected":False}
 print("PASS",v,"Cmd",ident,"=> 32B record => BEE_NewLayerTask<4> => virtual slot1 => stock layer creator => comp attach",flush=True)
result=root/"bee_newshape_full_native_command_to_comp_owner_cross_verified_2025_2026.json"
result.write_text(json.dumps({"evidence":"E2-L exact on-disk BEE static direct+vtable code chain; does not imply all conditional branches or foreign plugin ABI are valid","versions":proof},indent=2)+"\n")
print("SAVED",result)
