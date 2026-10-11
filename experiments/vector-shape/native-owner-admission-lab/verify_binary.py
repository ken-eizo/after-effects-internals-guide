"""Static release gate for the read-only owner/Contents admission AEGP.
Tests executable PE and forbidden source paths, NOT actual AE behavior.
"""
from pathlib import Path
import pefile,hashlib,json
home=Path(r"D:\Developer\ShapeLayerAE")
src=(home/"labs/native_owner_admission/NativeOwnerAdmission.cpp").read_text(encoding="utf8")
b=home/"build/native_owner_admission/Release/CNLNativeOwnerAdmission.aex"
assert b.is_file(),b
pe=pefile.PE(str(b))
assert pe.FILE_HEADER.Machine==0x8664
assert pe.OPTIONAL_HEADER.Magic==0x20b
assert pe.is_dll()
symbols={e.name.decode(errors="replace") for e in pe.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
assert "EntryPointFunc" in symbols,symbols
imports=[e.dll.decode(errors="replace").lower() for e in pe.DIRECTORY_ENTRY_IMPORT]
assert not any(x.startswith(("tdb.dll","bee.dll")) for x in imports),imports
for good in ("AEGP_GetNewStreamRefForLayer","AEGP_GetNewStreamRefByIndex",
             "AEGP_CanAddStream","AEGP_GetMatchName","AEGP_GetStreamGroupingType",
             "AEGP_GetNumStreamsInGroup","AEGP_DisposeStream"):
 assert good in src,good
for forbidden in ("AEGP_AddStream(","AEGP_DeleteStream(","RegisterFactoryFunc(",
                  "UnregisterFactoryFunc(","CreateNewMask(","AEGP_SetStreamValue(",
                  "AEGP_CreateNewComp(","AEGP_SetStreamValueAtTime("):
 assert forbidden not in src,forbidden
assert "kMaxNodes=240,kMaxDepth=4" in src
assert 'private_registry_invoked' in src and 'stream_created' in src
assert 'parent_link' in src and 'walk(s,out,child,depth+1,node' in src
data={"result":"compiled_release_static_pass_host_NOT_tested","sha256":hashlib.sha256(b.read_bytes()).hexdigest(),
"size":b.stat().st_size,"entrypoint":"EntryPointFunc","machine":"AMD64","import_dlls":imports,
"candidates":6,"bounded_max_nodes":240,"bounded_max_depth":4,"creates_host_stream":False}
dest=home/"results/native_owner_admission_build_receipt_20261012.json"
dest.write_text(json.dumps(data,indent=2)+"\n",encoding="utf8")
print("PASS x64 AEX export, no BEE/TDB direct imports, read-only suite calls and bounded traversal")
print("SHA256",data["sha256"],"bytes",data["size"])
print("SAVED",dest)
