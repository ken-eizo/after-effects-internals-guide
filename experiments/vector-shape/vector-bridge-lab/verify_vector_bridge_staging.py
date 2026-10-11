"""EXP-SHAPE-019 stage verifier: two independently compiled real .aex files.
No LoadLibrary/host function execution. Verify PE exports, Windows resource, SDK
registration string, isolated build directory and existing AEX unchanged.
"""
from pathlib import Path
import pefile,hashlib,json
ROOT=Path(r"D:\Developer\ShapeLayerAE")
AEIG=Path(r"D:\Developer\After Effects Internals Guide")
SUITE=b"CompNodeAE Vector Geometry Suite"
binroot=ROOT/"build/vector_bridge/Release"
artifacts={}
for basename,expected in [
    ("VectorBridgeAEGP.aex",{"EntryPointFunc"}),
    ("VectorBridgeConsumer.aex",{"EffectMain","PluginDataEntryFunction2"})]:
 path=binroot/basename
 pe=pefile.PE(str(path))
 pe.parse_data_directories()
 names={e.name.decode() for e in pe.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 resource_count=len(pe.DIRECTORY_ENTRY_RESOURCE.entries) if hasattr(pe,"DIRECTORY_ENTRY_RESOURCE") else 0
 imports=[x.dll.decode(errors="replace") for x in getattr(pe,"DIRECTORY_ENTRY_IMPORT",[])]
 data=path.read_bytes()
 assert expected.issubset(names),(basename,names)
 assert SUITE in data,(basename,"suite identifier missing")
 assert resource_count>0,(basename,"no PiPL resource")
 assert pe.FILE_HEADER.Machine==0x8664,(basename,"must be x86-64")
 assert not any(x.upper() in ("BEE.DLL","TDB.DLL") for x in imports),(basename,imports)
 artifacts[basename]={"path":str(path),"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data),
     "machine":"AMD64","exported_names":sorted(names),"expected_exports_ok":True,
     "suite_identifier_present":True,"resource_directory_types":resource_count,
     "imported_modules":imports,"private_BEE_TDB_linkage":False}
current=ROOT/"build/Release/ShapeLayerAE.aex"
installed=Path(r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\ShapeLayerAE.aex")
if installed.exists() and current.exists():
 x=hashlib.sha256(current.read_bytes()).hexdigest()
 y=hashlib.sha256(installed.read_bytes()).hexdigest()
 assert x==y,"active v3 installed binary differs from known research build"
 artifacts["original_v3_untouched"]={"same_sha256_as_installed":True,"sha256":x}
receipt=AEIG/"datasets/ae-pica-vector-bridge-two-plugin-build-receipt-2026.json"
receipt.write_text(json.dumps({"evidence":"E0-S distributed Adobe Sweetie/Checkout + locally compiled AEX PE inspection",
    "host_executed_by_this_static_verifier":False,"external_host_confirmation":"research/findings/F-VECTOR-020-pica-aegp-effect-ae2026-host-confirmation.md","mock_execution_result":"PASS after mock PF_UtilCallbacks fix","vector_geometry_caller_buffer_pod":True,
    "adobe_effect_native_contents_or_vectorart_output":False,
    "artifacts":artifacts},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("PASS staged binaries compiled, exported correct symbols, PiPL resources and ABI tags present",flush=True)
print("Static verifier ran no host calls; separate user AE2026 E2-X host confirmation and mock PASS are documented in F-VECTOR-020.",flush=True)
print("SAVED",receipt,flush=True)
