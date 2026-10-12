"""Cross-check real New Vector Layer command ID to exact internal BEE
command table callbacks on pinned AE2025 and AE2026, never executes Adobe.
"""
from pathlib import Path
import json,pefile,hashlib
base=Path(r"D:\Developer\ShapeLayerAE\results")
def load(name):return json.loads((base/name).read_text())["versions"]
commands=load("bee_native_comp_layer_attach_and_new_shape_command_2025_2026.json")
table=load("bee_native_command_table_32byte_entries_2025_2026.json")
handlers=load("bee_new_shape_exact_command_table_handlers_2025_2026.json")
graph=load("bee_newshape_command_handler_to_comp_creator_callgraph_2025_2026.json")
exps={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",101,"0xfecef0","0x646bd0","0x646c30","0x544470"),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",106,"0x104d270","0x660c10","0x660c70","0x563290")}
out={}
for year,(file,n,row,setup,execute,nextcall) in exps.items():
 p=pefile.PE(file)
 cmds=commands[year]["methods"]
 func=next(x for name,x in cmds.items() if name.startswith("?BEE_CmdNewVectorLayer@@"))
 instructions=[x["op"]+" "+x["args"] for x in func["instructions"][:5]]
 assert "mov edx, "+hex(n) in instructions
 assert "mov r8d, 0x306" in instructions
 assert any(x.startswith("jmp ") for x in instructions)
 t=table[year]["entries"][n]
 assert t["index"]==n and t["entry_rva"]==row
 assert t["pointers_rva"][1]==setup and t["pointers_rva"][2]==execute
 assert handlers[year]["new_shape_command_ID"]==n
 for slot,expected in (("callback_factory_plus8",setup),("callback_execution_plus16",execute)):
  assert handlers[year][slot]["rva"]==expected
 assert any(x.get("dest")==nextcall for x in handlers[year]["callback_execution_plus16"]["links"])
 assert graph[year]["handler_rva"]==execute
 assert graph[year]["direct_call_shortest_path"] is None
 assert graph[year]["max_depth"]==6
 assert handlers[year]["BEE_SHA256"]==hashlib.sha256(Path(file).read_bytes()).hexdigest()
 out[year]={"command_id":n,"command_resource_id":0x306,"table_item_rva":row,
  "callback_setup_rva":setup,"callback_execution_rva":execute,
  "execution_callback_next_native_target":nextcall,
  "native_ctor_comp_attach_direct_path_found_with_depth6":False,
  "static_functions_explored":graph[year]["functions_explored"],
  "external_CNL_extension_registered":False,
  "private_host_calls":0}
 print("PASS",year,"New Shape native cmd",n,"-> table",row,"-> handler",execute,"->",nextcall,flush=True)
target=base/"bee_newshape_command_id_to_native_table_verified_2025_2026.json"
target.write_text(json.dumps({"status":"PASS two versions of installed BEE native command ID and table mapping; no foreign Shape native type creation yet","versions":out},indent=2)+"\n")
print("SAVED",target)
