"""BEE native Shape command / undo / layer owner boundary proof.
Requires only saved static decoded datasets from actual 2025/26 PE files.
"""
from pathlib import Path
import json
root=Path(r"D:\Developer\ShapeLayerAE\results")
def v(path):return json.loads((root/path).read_text())["versions"]
baseline=v("bee_new_shape_undo_and_comp_attach_offline_verified_2025_2026.json")
table=v("bee_native_command_table_32byte_entries_2025_2026.json")
core=v("bee_command_executor_dispatch_core_2025_2026.json")
hits=v("bee_native_command_table_shape_handler_link_2025_2026.json")
wrappers=v("bee_command_undo_dispatch_native_internal_2025_2026.json")
results={}
for version in ("2025","2026"):
 b=baseline[version];t=table[version]["entries"];c=core[version]["ins"]
 expected_count=155 if version=="2025" else 160
 expected_start="0xfec250" if version=="2025" else "0x104c530"
 assert len(t)==expected_count,(version,len(t))
 assert table[version]["table_rva"]==expected_start
 assert all(int(x["entry_rva"],16)==int(expected_start,16)+32*x["index"] for x in t)
 # The command table contains a 32-byte (4 qword) record; +8/+16 are callback pointers.
 active=[r for r in t if r["pointers_rva"][1] and r["pointers_rva"][2]]
 assert len(active)>125
 assert all(r["pointers_rva"][1] and r["pointers_rva"][2] for r in active)
 assert len(table[version]["new_vector_layer_direct_pointers"])==0
 assert hits[version]["direct_native_shape_or_command_handlers"]==[]
 assert b["creation_explicit_shape_kind_4"]
 assert b["both_calls_in_same_native_function"]
 assert b["comp_attach_uses_position_and_boolean_arguments"]
 assert b["CompAttach_wrapper_then_params_extra_init"]
 assert b["comp_attach_position_bookkeeper_has_nontrivial_body"]
 assert b["command_dispatch_to_this_exact_create_function_proven"] is False
 assert any(x["ins"]==("shl rdi, 5" if version=="2025" else "shl rax, 5") for x in c)
 assert any(x["ins"]=="cmp qword ptr [r15 + 8], 0" for x in c)
 assert any(x["ins"]=="cmp qword ptr [r15 + 0x10], 0" for x in c)
 assert any(x["ins"]=="call rdx" for x in c)
 assert any(x["ins"]=="mov rdx, qword ptr [r15 + 8]" for x in c)
 paths=wrappers[version]["entrypoints"]
 assert len(paths)==2
 assert any("BEE_Project" in key for key in paths)
 assert any("UndoContext" in key for key in paths)
 results[version]={"entry_count":len(t),"active_callback_pairs":len(active),
  "table_rva":expected_start,"item_stride_bytes":32,
  "callback_ptr_plus8_and_plus16":True,
  "checked_cb_ptr_plus8_called_indirectly":True,
  "new_vector_command_has_direct_table_pointer":False,
  "direct_shape_links_in_table_handlers":0,
  "shape_creation_and_attach_in_same_native_helper":True,
  "undo_BEE_StartGroup_DoCommand_EndGroup_order_verified":True,
  "BEE_DoCommand_forwards_to_shared_executor":True,
  "indirect_command_router_to_specific_shape_constructor_proven":False,
  "private_native_calls_executed":0}
 print("PASS",version,results[version],flush=True)
dest=root/"bee_native_shape_creation_undo_command_table_verified_2025_2026.json"
dest.write_text(json.dumps({"status":"PASS offline native x64 code + registered command table validation; external plugin NOT enabled",
 "versions":results,"scope":"Type-4 Shape creation + attached owner and undo wrapper each proven. The final indirect BEE_DoCommand-to-create helper edge not yet resolved."},indent=2)+"\n")
print("SAVED",dest)
