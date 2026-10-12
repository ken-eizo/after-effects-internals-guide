"""BEE_NewLayerTask<4> native command object 0x30-byte layout cross-version
from on-disk x64 constructors and virtual execution + serialization code.
"""
from pathlib import Path
import json,hashlib
folder=Path(r"D:\Developer\ShapeLayerAE\results")
def load(name):return json.loads((folder/name).read_text())["versions"]
ctors=load("bee_newshape_task4_native_command_object_constructor_layout_2025_2026.json")
callbacks=load("bee_new_shape_exact_command_table_handlers_2025_2026.json")
vt=load("bee_newshape_task4_vtable_virtual_calltargets_2025_2026.json")
names=load("bee_new_shape_command_object_rtti_vtable_2025_2026.json")
out={}
for y in ("2025","2026"):
 init,restore=ctors[y]
 lines=[x["ins"] for x in init["instructions"]]
 assert "mov esi, r8d" in lines
 assert "mov dword ptr [rdi + 0x28], esi" in lines
 assert "vmovups ymmword ptr [rdi + 8], ymm0" in lines
 assert "mov qword ptr [rdi], rax" in lines
 assert any(x["op"]=="mov r8d, 4" for x in callbacks[y]["callback_factory_plus8"]["instructions"])
 assert "BEE_NewLayerTask" in names[y]["RTTI_Cpp_class_decorated"]
 slot1=[x["op"]+" "+x["args"] for x in vt[y]["virtuals"][1]["first_instructions"]]
 assert "mov ecx, dword ptr [rbx + 0x28]" in slot1
 slot2=vt[y]["virtuals"][2]["calls"]
 ser=sum("AddToObject@serialization@dvacore" in x.get("target_symbol","") for x in slot2)
 assert ser>=5
 restore_lines=[x["ins"] for x in restore["instructions"]]
 assert "mov dword ptr [rbx + 0x28], eax" in restore_lines
 assert any(x.startswith("mov qword ptr [rbx + 8],") for x in restore_lines)
 out[y]={"native_task_allocation_bytes":48,
  "vtable_offset":0,
  "copied_command_context_offset":8,
  "copied_command_context_bytes":32,
  "layer_kind_offset":40,
  "newshape_layer_kind_value":4,
  "constructor_writes_kind_from_arg8":True,
  "exec_uses_kind_at_0x28":True,
  "alternate_constructor_restores_kind_from_command_info":True,
  "virtual_slot2_dvacore_serialize_AddToObject_calls":ser,
  "safe_CNL_abi_declared":False}
 print("PASS",y,"0x30 byte NewShape command task type4 field +0x28; serializable Undo task",flush=True)
outpath=folder/"bee_newshape_task4_layout_and_undo_serialization_verified_2025_2026.json"
outpath.write_text(json.dumps({"evidence":"E2-L exact pinned AE2025/26 BEE compiled constructors and virtual methods; no in-host private methods executed","versions":out},indent=2)+"\n")
print("SAVED",outpath)
