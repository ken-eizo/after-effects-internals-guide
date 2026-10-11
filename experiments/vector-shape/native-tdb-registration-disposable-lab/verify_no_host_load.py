"""EXP-SHAPE-030: inspect risky, NOT HOST-TESTED AEX build gates statically.

Only compiled PE inspection/source audit, NEVER load the AEX into AE.
"""
from pathlib import Path
import hashlib,json,pefile,re
root=Path(r"D:\Developer\ShapeLayerAE")
aex=root/"build/native_tdb_registration_disposable/Release/CNLPrivateTDBDisposable.aex"
source=(root/"labs/native_tdb_registration_disposable/CNLPrivateTDBDisposable.cpp").read_text(encoding="utf8")
assert aex.exists()
pe=pefile.PE(str(aex))
assert pe.FILE_HEADER.Machine==0x8664
exports={x.name.decode(errors="replace") for x in pe.DIRECTORY_ENTRY_EXPORT.symbols if x.name}
assert "EntryPointFunc" in exports
deps={entry.dll.decode(errors="replace").lower() for entry in pe.DIRECTORY_ENTRY_IMPORT}
assert "tdb.dll" not in deps and "bee.dll" not in deps and "agm.dll" not in deps
binary=aex.read_bytes()
guards=[
"CNL_TDB_DISPOSABLE_HOST_TEST",
"I_ACCEPT_PRIVATE_REGISTRY_CRASH_RISK",
"CNL_TDB_DISPOSABLE_ACK.flag",
"CNL_TDB_ONLY_DISPOSABLE_NO_REAL_PROJECTS",
"DeleteFileA",
"GetModuleHandleW",
"hashModule",
"pinned(digest)",
"VirtualQuery",
"GetProcAddress",
"active_layer_not_allowed",
"before_private_register_factory_func",
"before_private_unregister_factory_func",
"unregister_result",
]
for g in guards:
 assert g in source,(g,"missing in source")
assert b"CNL Private TDB: Disposable Type Registration (DANGER)" in binary
assert source.count("reinterpret_cast<NativeRegister>(reg)") == 1
assert source.count("reinterpret_cast<NativeUnregister>(unreg)") == 1
# Both call expressions are guarded inside Run() and no explicit/private API calls
# appear in EntryPointFunc (the AEGP initialization path).
entry=source.split('A_Err EntryPointFunc(')[1]
assert "RegisterFactoryFunc" not in entry
assert "reinterpret_cast<Native" not in entry
assert "Run();" in source.split("A_Err CommandHook(")[1]
# This verifier only checks static guard presence, NOT proof that host-private
# code is safe to execute or that rollback can be relied on.
receipt={
"experiment":"EXP-SHAPE-030",
"date":"2026-10-12",
"status":"compiled-static-gates-unexecuted-high-risk",
"file":str(aex),
"sha256":hashlib.sha256(binary).hexdigest(),
"bytes":len(binary),
"machine":"x64",
"symbols":sorted(exports),
"hard_imports":sorted(deps),
"contains_mutating_private_Adobe_calls":True,
"private_registry_called":False,
"AE_installed_by_researcher":False,
"AE_host_tested":False,
"manual_menu":"Animation > CNL Private TDB: Disposable Type Registration (DANGER)",
"one_shot_manual_ack_required":True,
"pin_exact_loaded_DLL_sha256":True,
"native_creation_callback":"TDB_ParamPathStream::Create (Adobe, non-Shape parameter native stream)",
"test_intent":"new MatchName registry acceptance and immediate attempt to unregister",
"no_standalone_validity_claim":True,
"uncertainty":"Can crash/corrupt AE. No complete host-native editor/owner/render integration. Do not use before separate safe preflight and explicit user risk acceptance."
}
dest=root/"results/native_tdb_disposable_build_receipt_20261012.json"
dest.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("PASS PE structure and manually guarded private mutation source is present")
print("WARNING: ZERO real AE test, UNKNOWN host safety, rollback NOT PROVEN")
print("SHA256",receipt["sha256"])
print("SAVED",dest)
