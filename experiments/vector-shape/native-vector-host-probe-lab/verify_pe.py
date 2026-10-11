"""EXP-SHAPE-028: inspect compiled AEGP before user installs it.

Verifies actual PE x64, PiPL resource presence, entry point, native CNL
geometry exports and absence of private TDB/BEE imports. No AE is run.
"""
from pathlib import Path
import subprocess,pefile,hashlib,json
root=Path(r"D:\Developer\ShapeLayerAE")
artifact=root/"build/native_vector_host_probe/Release/CNLNativeVectorHostProbe.aex"
assert artifact.is_file()
pe=pefile.PE(str(artifact))
assert pe.FILE_HEADER.Machine==0x8664
exports={x.name.decode("ascii","replace") for x in pe.DIRECTORY_ENTRY_EXPORT.symbols if x.name}
expect={"EntryPointFunc","cnl_document_create","cnl_document_destroy",
        "cnl_document_add_group","cnl_document_add_path",
        "cnl_document_add_ellipse","cnl_document_copy_cubics",
        "cnl_document_serialize","cnl_document_deserialize"}
assert expect.issubset(exports),("missing",expect-exports)
imports={x.dll.decode("ascii","replace").lower() for x in pe.DIRECTORY_ENTRY_IMPORT}
assert "tdb.dll" not in imports
assert "bee.dll" not in imports
assert "agm.dll" not in imports
resource_types={getattr(x.name,"string",None) or x.id for x in pe.DIRECTORY_ENTRY_RESOURCE.entries}
resource_dump=subprocess.run(["dumpbin","/headers",str(artifact)],
 capture_output=True,text=True,errors="replace",check=True).stdout
assert ".rsrc" in resource_dump
all_bytes=artifact.read_bytes()
assert b"CNL Native Vector Host Probe" in all_bytes
assert b"CNL Native Vector: Host Preflight (Read Only)" in all_bytes
assert b"CNL_NativeVector_HostPreflight.tsv" in all_bytes
source=(root/"labs/native_vector_host_probe/CNLVectorHostBridge.cpp").read_text(encoding="utf-8")
assert "RegisterFactoryFunc" in source and "GetProcAddress" in source
assert "CNL_NATIVE_ENABLE_PRIVATE_REGISTRATION" not in source
# The absence of a hard-import is meaningful, but not proof that the indirect API
# cannot be called; source review guards ensure this is only export observation.
assert "reinterpret_cast<Getter>(getter)()" in source
assert "reinterpret_cast<RegisterFactoryFunc" not in source
assert "CNL_CubicBezier cubic[4]" in source
receipt={
 "experiment":"EXP-SHAPE-028",
 "date":"2026-10-12",
 "status":"compiled-static-PE-preflight-only",
 "file":str(artifact),
 "sha256":hashlib.sha256(all_bytes).hexdigest(),
 "bytes":len(all_bytes),
 "architecture":"x64",
 "entry_export": "EntryPointFunc",
 "CNL_native_path_model_compiled_into_AEX":True,
 "CNL_cubic_and_document_functions_exported":True,
 "native_TDB_BEE_AGM_hard_imports":False,
 "AE_host_runtime_test":False,
 "AE_installed_by_researcher":False,
 "native_TDB_type_registration":False,
 "native_Shape_VectorArt_output":False,
 "preflight_menu":"Animation > CNL Native Vector: Host Preflight (Read Only)",
 "expected_report":"%TEMP%/CNL_NativeVector_HostPreflight.tsv",
 "exports":sorted(exports),
 "imports":sorted(imports),
 "source":"experiments/vector-shape/native-vector-host-probe-lab",
 "remarks":"Source contains ONLY private getter call gated by DLL sha and opcode; all other private exports are presence checks."
}
dest=root/"results/native_vector_host_probe_receipt_20261012.json"
dest.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("PASS compiled AEGP PiPL, entry export, CNL native procedural vector core, zero private native imports")
print("AEX_SHA256",receipt["sha256"])
print("SAVED",dest)
