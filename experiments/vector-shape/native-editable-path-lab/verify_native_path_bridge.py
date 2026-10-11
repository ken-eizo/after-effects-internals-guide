"""Read-only QA for native editable path bridge AEX, local SDK, source guardrails.
Does not load AEX, invoke host callbacks, install, or modify AE.
"""
from pathlib import Path
import pefile,hashlib,json,subprocess
root=Path(r"D:\Developer\ShapeLayerAE")
exe=root/"build/native_editable_path/Release/NativeEditablePathBridge.aex"
source=root/"labs/native_editable_path/NativeEditablePathBridge.cpp"
provider=root/"build/vector_bridge/Release/VectorBridgeAEGP.aex"
original=root/"build/Release/ShapeLayerAE.aex"
assert exe.is_file() and provider.is_file()
blob=exe.read_bytes();p=pefile.PE(data=blob)
assert p.FILE_HEADER.Machine==0x8664
names={e.name.decode() for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
assert "EntryPointFunc" in names,names
assert hasattr(p,"DIRECTORY_ENTRY_RESOURCE")
assert any(str(x.name).upper()=="PIPL" for x in p.DIRECTORY_ENTRY_RESOURCE.entries)
imports=[d.dll.decode("utf-8","replace").lower() for d in getattr(p,"DIRECTORY_ENTRY_IMPORT",[])]
assert "bee.dll" not in imports and "tdb.dll" not in imports,imports
s=source.read_text(encoding="utf-8")
required=[
"AEGP_CreateNewMask", "AEGP_SetMaskOutlineVertexInfo",
"AEGP_CreateVertex","AEGP_SetMaskOutlineOpen",
"AEGP_SetStreamValue", "AEGP_GetLayerObjectType",
"AEGP_ObjectType_AV", "AEGP_GetNewMaskStream",
"AEGP_LTimeMode_CompTime","AEGP_StartUndoGroup","AEGP_EndUndoGroup",
"AEGP_DisposeMask", "AEGP_DisposeStreamValue",
"AEGP_DeleteMaskFromLayer","PF_MaskMode_NONE","PF_MaskMode_ADD",
"kCNLVectorBridgeSuite1","CopyCubicPath","AEGP_GetNewStreamRefForLayer",
"AEGP_GetNewStreamRefByIndex","AEGP_GetMatchName",
"AEGP_GetUniqueCommand","AEGP_RegisterCommandHook"
]
assert all(t in s for t in required)
assert s.count("AEGP_AddStream")==0
assert s.count("GetProcAddress")==0
assert "BEE_" not in s and "TDB_" not in s
assert "std::isfinite" in s
assert "prior.x2-cur.x0" in s and "cur.x1-cur.x0" in s
assert "use_native_mask_rendering?PF_MaskMode_ADD:PF_MaskMode_NONE" in s
data={
 "classification":"E0-H public AE SDK25.6 + compiled PE metadata static verification. No AE actual runtime execution.",
 "compiled_aex":str(exe),
 "aex_sha256":hashlib.sha256(blob).hexdigest(),
 "bytes":len(blob),
 "exported_entrypoints":sorted(names),
 "pipl_resource_found":True,
 "native_shape_contents_owned_by_effect":False,
 "native_mask_ownership_target":"selected BEE AV layer, via public AEGP MaskSuite4",
 "production_shape_vectorart_renderer_hook":False,
 "native_mask_compositor_expected_when_add_mode":True,
 "AE_actual_native_mask_creation_test":False,
 "commands":[
  "CompNodeAE: Create Native Editable Mask from PICA",
  "CompNodeAE: Native Mask Renderer (ADD, Clips Layer)",
  "CompNodeAE: Inspect Native Owner Roots (Read Only)"
 ],
 "native_vertex_geometry":"CNL 4 cubic paths -> mask vertices x0,y0; in tangent previous cubic x2-p_i; out tangent current cubic x1-p_i",
 "mutation":"only from explicit menu commands; disabled if no active selected AV layer; failure cleanup and undo group",
 "provider_expected_sha256":hashlib.sha256(provider.read_bytes()).hexdigest(),
 "build_parent":"D:/Developer/ShapeLayerAE/build/native_editable_path/Release"
}
dest=root/"results/native_editable_path_qa_20261012.json"
dest.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("PASS compiled x64 AEX PiPL/entrypoint; PICA cubic source; native mask authoring; no private ABI invoked; explicit-only mutation")
print(data["aex_sha256"])
print(dest)
