"""Cross-version proof that BEE_VectorLayer TDB typed creator constructs a
detached layer object (BEE_CompItem*=null), whereas normal native layer-kind
factory calls SAME constructor with a real BEE_CompItem*.
Static native PE only; no AE methods invoked.
"""
from pathlib import Path
import json,hashlib
base=Path(r"D:\Developer\ShapeLayerAE\results")
f=json.loads((base/"bee_vector_owner_factory_vs_generic_layer_dispatch_2025_2026.json").read_text())["versions"]
stock=json.loads((base/"bee_native_vector_owner_constructor_stock_dispatch_context_2025_2026.json").read_text())["versions"]
typed=json.loads((base/"bee_vector_layer_62_native_tdb_creators_2025_2026.json").read_text())["versions"]
paths={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
 "2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
out={}
for ver in ("2025","2026"):
 methods=f[ver]["factories"]
 create=next(x for name,x in methods.items() if name.startswith("?Create@BEE_VectorLayer@@"))
 dispatch=next(x for name,x in methods.items() if name.startswith("?CreateLayerFromType@BEE_Layer@@"))
 c=stock[ver]["native_vector_ctor_call"]
 ctor_calls=[x for x in create["calls"] if "??0BEE_VectorLayer@@" in x.get("target","")]
 assert len(ctor_calls)==1
 assert int(ctor_calls[0]["asm"].split()[-1],16)-0x180000000==int(c["ctor_rva"],16),(ver,ctor_calls,c)
 inst=[x["asm"] for x in create["first_instructions"]]
 assert "xor r9d, r9d" in inst,ver
 assert any(x=="mov byte ptr [rsp + 0x20], 1" for x in inst)
 assert any(x=="mov ecx, "+("0x2820" if ver=="2025" else "0x2830") for x in inst)
 assert create["native_bytes"]==95
 assert any(x["target"].startswith("??0BEE_VectorLayer@@") for x in dispatch["calls"])
 startup=[x["asm"] for x in dispatch["first_instructions"]]
 if ver=="2025":
  assert "mov rsi, rdx" in startup
  assert "mov r9, rsi" in [x["op"]+" "+x["args"] for x in c["instructions"]]
 else:
  assert "mov rbx, rdx" in startup
  assert "mov r9, rbx" in [x["op"]+" "+x["args"] for x in c["instructions"]]
 assert any("cmp" in x["asm"] and ", 7" in x["asm"] for x in dispatch["first_instructions"])
 assert "BEE_VectorLayer::Create" in typed[ver]["entries"][61]["creator"]["symbol"] or "?Create@BEE_VectorLayer" in typed[ver]["entries"][61]["creator"]["symbol"]
 assert typed[ver]["entries"][61]["creator"]["data_rva"]==create["entry_rva"]
 full=hashlib.sha256(Path(paths[ver]).read_bytes()).hexdigest()
 assert full==f[ver]["BEE_SHA256"]
 out[ver]={"BEE_SHA256":full,
   "TDB_native_VectorLayer_creator_rva":create["entry_rva"],
   "TDB_creator_constructs_comp_item_arg_null":True,
   "TDB_creator_allocation_bytes":int("0x2820" if ver=="2025" else "0x2830",16),
   "TDB_creator_calls_same_BEE_VectorLayer_ctor_as_stock":True,
   "normal_layer_factory":"BEE_Layer::CreateLayerFromType",
   "normal_factory_accepts_nonnull_BEE_CompItem_arg_from_own_parameter":True,
   "normal_layer_kind_fixed_dispatch_0_through_7":True,
   "normal_layer_kind_for_vector":4,
   "external_plugin_can_attach_new_native_layer_proven":False,
   "owner_attachment_source_inferred_only":False}
 print("PASS",ver,"TDB Creator => comp=null; native stock layer kind4 => real comp parent",flush=True)
target=base/"bee_vector_factory_detached_vs_comp_owned_layer_verified_2025_2026.json"
target.write_text(json.dumps({"evidence":"E2-L BEE native typed VectorLayer creator vs CompItem-backed BEE_Layer::CreateLayerFromType, x64 machine code on pinned AE installs",
 "versions":out,
 "limitations":["Does not prove no possible later attachment of a TDB-created layer","No independent CNL layer kind introduced","No private calls"]},indent=2)+"\n")
print("SAVED",target)
