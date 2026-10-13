"""PE-level verification for new independent native Shape runtime AEX.
Fails if exported AEGP, CNL native C ABI, or PiPL missing; any Adobe private
BEE/TDB import is prohibited. Never loads the DLL in After Effects.
"""
from pathlib import Path
import pefile,hashlib,json
root=Path(r"D:\Developer\ShapeLayerAE")
p=root/"build/native_shape_layer_prototype/Release/CNLNativeShapeLayer.aex"
assert p.is_file()
data=p.read_bytes();pe=pefile.PE(data=data)
exports={x.name.decode(errors="replace") for x in pe.DIRECTORY_ENTRY_EXPORT.symbols if x.name}
required={"EntryPointFunc","cnl_shape_create","cnl_shape_destroy","cnl_shape_features",
"cnl_shape_add_group","cnl_shape_add_path","cnl_shape_add_ellipse",
"cnl_shape_set_vertex","cnl_shape_move_node","cnl_shape_get_vertex",
"cnl_shape_contents_root","cnl_shape_undo","cnl_shape_redo",
"cnl_shape_archive","cnl_shape_from_archive","cnl_shape_svg",
"cnl_shape_undo_depth","cnl_shape_redo_depth",
"cnl_document_create","cnl_document_destroy"}
assert required<=exports,required-exports
imports={desc.dll.decode(errors="replace").lower():[
x.name.decode(errors="replace") if x.name else "#"+str(x.ordinal)
for x in desc.imports] for desc in pe.DIRECTORY_ENTRY_IMPORT}
assert all("tdb.dll"!=k and "bee.dll"!=k and "flt.dll"!=k for k in imports)
assert all(not any("TDB_" in n or "BEE_" in n for n in v) for v in imports.values())
pipl=[]
for typ in pe.DIRECTORY_ENTRY_RESOURCE.entries:
 if typ.name is not None:
  tn=str(typ.name)
  if "PIPL" in tn.upper():
   pipl.append(tn)
 else:
  # type RCDATA in the PiPL-compiled resource or custom numeric type
  pipl.append(str(typ.id))
assert "PIPL" in [x.upper() for x in pipl],pipl
src=(root/"labs/native_shape_layer_prototype/NativeShapeLayerPlugin.cpp").read_text()
assert "AEGP_RegisterCommandHook" in src and "AEGP_InsertMenuCommand" in src
assert "AEGP_Menu_NEW" in src and "ChapeLayer (Native Type Pending)" in src
assert "CNL_RunChapeHostProbe" in src
assert "ChapeLayer_MenuRegistration.tsv" in src
assert "AEGP_Menu_LAYER" in src and "ChapeLayer: Native Type Status (Fallback)" in src
assert 'AEGP_Menu_NEW,AEGP_MENU_INSERT_AT_TOP' in src

probe=(root/"labs/native_shape_layer_prototype/ChapeHostAdmissionProbe.cpp").read_text()
assert "AEGP_CanAddStream(" in probe
assert "cnl_evaluation_trace" in probe and "indexed_child" in probe
assert "contents=rootVectors;" in probe
assert "kind!=AEGP_StreamGroupingType_NAMED_GROUP" in probe
assert "AEGP_GetNewStreamRefByIndex" in probe
assert "if(contents)s.StreamSuite2()->AEGP_DisposeStream(contents);" not in probe

assert all(name not in probe for name in ("AEGP_AddStream(", "AEGP_DeleteStream(", "RegisterFactoryFunc(", "GetProcAddress("))
assert all(x not in src for x in ("GetProcAddress(", "AEGP_AddStream(","AEGP_NewLayer(","PF_Cmd_"))
result={"status":"PASS","file":str(p),"sha256":hashlib.sha256(data).hexdigest(),
"size_bytes":len(data),"arch":"x64" if pe.FILE_HEADER.Machine==0x8664 else hex(pe.FILE_HEADER.Machine),
"entrypoint_exported":True,"CNL_c_abi_export_count":len([e for e in exports if e.startswith("cnl_")]),
"pipl_resource_types":pipl,"private_TDB_BEE_FLT_imports":False,
"AE_host_private_functions_executed":False,
"AE_native_Timeline_owner_created":False,
"AE_Pen_integrated":False}
target=root/"results/cnl_native_shape_prototype_static_receipt_20261012.json"
target.write_text(json.dumps(result,indent=2)+"\n")
print("PASS native prototype AEX x64/PiPL/AEGP/CNL C-ABI/private import gate",result["sha256"],"CNL exports",result["CNL_c_abi_export_count"])
