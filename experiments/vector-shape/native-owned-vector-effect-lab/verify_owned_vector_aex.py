"""Read-only PE/SDK contract verification for CNL-owned vector AEX.
Run the compiled host mock. No After Effects GUI, project or private API.
"""
from pathlib import Path
import hashlib,json,os,subprocess,pefile
SRC=Path(__file__).resolve().parent
ROOT=SRC.parent.parent if SRC.parent.name=="labs" else SRC
default_build=ROOT/"build"/"native_vector_document_effect" if SRC.parent.name=="labs" else SRC/"build"
BUILD=Path(os.environ.get("CNL_OWNED_EFFECT_BUILD",str(default_build)))/"Release"
AEX=BUILD/"CNLOwnedVectorEffect.aex"
MOCK=BUILD/"OwnedVectorHostMock.exe"
pipl=(SRC/"CNLOwnedVectorEffect_PiPL.r").read_text(encoding="utf-8-sig")
cpp=(SRC/"CNLOwnedVectorEffect.cpp").read_text(encoding="utf-8")
raw=AEX.read_bytes()
pe=pefile.PE(data=raw)
exports={x.name.decode(errors="replace") for x in pe.DIRECTORY_ENTRY_EXPORT.symbols if x.name}
needed={"EffectMain","PluginDataEntryFunction2","cnl_document_create",
        "cnl_document_deserialize","cnl_document_serialize","cnl_document_set_vertex",
        "cnl_document_copy_cubics"}
assert needed <= exports,(needed-exports)
imports={imp.dll.decode(errors="replace").lower() for imp in pe.DIRECTORY_ENTRY_IMPORT}
assert not any(x in imports for x in ("tdb.dll","bee.dll","flt.dll","adobe after effects.exe"))
assert all(x in cpp for x in (
 "PF_Cmd_ARBITRARY_CALLBACK","PF_Arbitrary_COPY_FUNC",
 "PF_Arbitrary_FLATTEN_FUNC","PF_Arbitrary_UNFLATTEN_FUNC",
 "PF_Arbitrary_INTERP_FUNC","PF_Arbitrary_COMPARE_FUNC",
 "PF_PUI_NO_ECW_UI","PF_ADD_ARBITRARY2","cnl_document_deserialize",
 "cnl_document_copy_cubics","cnlvec::Draw"))
assert not any(x in cpp for x in (
 "RegisterFactoryFunc","UnregisterFactoryFunc","AEGP_CreateMask",
 "AEGP_CreateNewMask","PF_Param_PATH","BEE_GetStreamWithSpec"))
assert 'AE_Effect_Match_Name { "CNL Owned Vector Document" }' in pipl
assert "AE_Effect_Global_OutFlags_2 { 0x8000000 }" in pipl
assert any(section.Name.rstrip(b"\0")==b".rsrc" for section in pe.sections)
result=subprocess.run([str(MOCK),str(AEX)],capture_output=True,
                      text=True,timeout=30,check=True)
assert "PASS AE effect-owned archive lifecycle" in result.stdout
assert "copy/flatten/unflatten/corrupt/compare/interp/print-scan/dispose clean" in result.stdout
receipt={"status":"pass-offline-only","classification":"new CNL-owned arbitrary doc and CPU-raster effect; NOT AE-native Contents/Pen/BEE_VectorArt",
 "AEX":str(AEX),"AEX_sha256":hashlib.sha256(raw).hexdigest(),
 "AEX_size":len(raw),"AEX_machine":hex(pe.FILE_HEADER.Machine),
 "PE_exports_present":sorted(needed),"imported_modules":sorted(imports),
 "PiPL_match_name":"CNL Owned Vector Document",
 "mask_shape_carrier_used":False,"private_BEE_TDB_FLT_module_imports":False,
 "archive_callbacks":"NEW/DISPOSE/COPY/SIZE/FLATTEN/UNFLATTEN/INTERP/COMPARE/PRINT/SIZE/SCAN reversible HEX with invalid scan rejection",
 "render":"native CNL cubic document --> single CPU 8bpc PF_World",
 "host_mock_stdout":result.stdout.strip(),
 "host_AE_installation_tested":False,
 "host_AE_save_reopen_tested":False,
 "host_native_Pen_or_VectorArt":False}
target=(ROOT/"results" if SRC.parent.name=="labs" else SRC/"results")/"owned_vector_effect_offline_build_receipt_20261012.json"
target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("PASS PE exports / PiPL / dependency block / callbacks / nested geometry renderer")
print(result.stdout.strip())
print("AEX SHA256",receipt["AEX_sha256"])
print("SAVED",target)
