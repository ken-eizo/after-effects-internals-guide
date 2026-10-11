"""Release verification: actual PE exports, imports, CTest, ctypes.
No Adobe host runtime, AEX, or installation invoked.
"""
from pathlib import Path
import json,hashlib,subprocess,pefile
root=Path(r"D:\Developer\ShapeLayerAE")
dll=root/"build/native_vector_core/Release/CNLNativeVectorCore.dll"
assert dll.exists()
p=pefile.PE(str(dll))
assert p.FILE_HEADER.Machine==0x8664
exports={x.name.decode("utf8") for x in p.DIRECTORY_ENTRY_EXPORT.symbols if x.name}
expected={
"cnl_core_version","cnl_document_create","cnl_document_destroy",
"cnl_document_clone","cnl_document_root","cnl_document_add_group",
"cnl_document_add_path","cnl_document_add_ellipse",
"cnl_document_copy_cubics","cnl_document_move_node",
"cnl_document_get_kind","cnl_document_get_parent",
"cnl_document_get_child_count","cnl_document_get_child",
"cnl_document_get_name","cnl_document_get_path_info",
"cnl_document_get_vertex","cnl_document_set_vertex",
"cnl_document_serialize","cnl_document_deserialize"
}
assert expected==exports,("missing",expected-exports,"extra",exports-expected)
imports={x.dll.decode("utf8","replace").lower() for x in p.DIRECTORY_ENTRY_IMPORT}
assert not any("adobe" in x or x in ("tdb.dll","bee.dll","agmf.dll","agm.dll") for x in imports)
def run(cmd):
 v=subprocess.run(cmd,capture_output=True,text=True,errors="replace")
 if v.returncode:raise RuntimeError(f"{cmd} exit {v.returncode}: {v.stderr} {v.stdout}")
 return (v.stdout+v.stderr).strip()
ctest=run(["ctest","--test-dir",str(root/"build/native_vector_core"),"-C","Release","--output-on-failure"])
assert "100% tests passed" in ctest
ctypes=run(["python",str(root/"labs/native_vector_core/test_external_c_abi.py")])
assert ctypes.startswith("PASS Python ctypes")
receipt={
"date":"2026-10-12",
"evidence":"E2-B: compiled x64 C++ native reusable library, independent tests",
"goal":"host-independent authorable vector Contents tree with real cubic data, to be adapted to native AE host ownership later",
"library_path":str(dll),
"sha256":hashlib.sha256(dll.read_bytes()).hexdigest(),
"architecture":"Windows AMD64",
"actual_export_count":len(exports),
"exported_C_API_functions":sorted(exports),
"imports":sorted(imports),
"runtime_CTest":"PASS",
"runtime_external_ctypes":"PASS",
"features":["native double-precision tangent/vertex data","64-bit typed node identities","indexed hierarchical Contents with child ownership","tree relocation with cycle rejection","stable deep clone","versioned checksum archive, canonical deterministic roundtrip","native Bezier cubic retrieval, closed or open","code-generated ellipse returns four cubic segments","bad archive and bad value rejection","iterative serialization handles 2048 nested groups"],
"limitations":["NOT an Adobe AE Shape Layer/Mask object","NOT yet registered as TDB_StreamBase or BEE evaluator","NO native After Effects Timeline/Pen/Selection/VectorArt/RG hookup","archive belongs to CompNodeAE, NOT AEP/SLU native format","document objects not thread-safe: caller must serialize own writes","independent Windows DLL, not a usable .aex by itself"],
"AE_rendering_or_plugin_test":"NOT RUN",
"private_registry_calls_made":False,
"installation_or_AE_UI_access":False,
"ctest_stdout_last_lines":ctest.splitlines()[-6:],
"ctypes_stdout":ctypes
}
dest=root/"results/native_vector_core_release_receipt_20261012.json"
dest.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("PASS native x64 DLL ABI, full C API, no Adobe imports, CTest, cross-language external ctypes")
print("SHA256",receipt["sha256"])
print("SAVED",dest)
