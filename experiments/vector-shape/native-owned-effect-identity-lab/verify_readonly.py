"""Confirm new native CNL effect ID AEGP is read-only and version-pinned.
Offline PE/static contract; does not load into After Effects.
"""
from pathlib import Path
import pefile,hashlib,json,os,re
root=Path(__file__).resolve().parent
code=(root/"CNLArchiveIdentity.cpp").read_text(encoding="utf-8")
pipl=(root/"CNLArchiveIdentity_PiPL.r").read_text(encoding="utf-8")
exe=Path(os.environ.get("CNL_EFFECT_IDENTITY_AEX",r"D:\Developer\ShapeLayerAE\build\native_owned_archive_identity\Release\CNLArchiveIdentity.aex"))
p=pefile.PE(str(exe))
exports={x.name.decode(errors="replace") for x in p.DIRECTORY_ENTRY_EXPORT.symbols if x.name}
assert "EntryPointFunc" in exports
imports={r.dll.decode(errors="replace").lower() for r in p.DIRECTORY_ENTRY_IMPORT}
assert not imports.intersection({"tdb.dll","bee.dll","flt.dll","afterfx.exe"})
needed=["AEGP_GetEffectNumParamStreams","AEGP_GetNewEffectStreamByIndex",
 "AEGP_GetEffectParamUnionByIndex","AEGP_GetStreamType",
 "AEGP_GetUniqueStreamID","AEGP_CanVaryOverTime","AEGP_GetMatchName",
 "AEGP_GetEffectMatchName","AEGP_DisposeEffect","AEGP_DisposeStream"]
assert all(x in code for x in needed)
for disallow in ("AEGP_SetStreamValue","AEGP_AddStream(","AEGP_DeleteStream(",
 "AEGP_ApplyEffect(","AEGP_RemoveEffect","AEGP_SetEffectFlags",
 "RegisterFactoryFunc","UnregisterFactoryFunc","AEGP_GetNewStreamValue",
 "AEGP_GetNewKeyframeValue"):
 assert disallow not in code,disallow
assert 'Kind { AEGP }' in pipl and 'CodeWin64X86 { "EntryPointFunc" }' in pipl
assert "CNL Effect Native Stream Identity (Read Only)" in pipl
assert "CNL Owned Vector Document" in code
assert "CNL_OwnedEffect_StreamIdentity.tsv" in code
assert "opaque_arb_payload_read\\t0" in code
assert p.FILE_HEADER.Machine==0x8664
receipt={"status":"PASS offline x64 PE + source read-only audit; not yet AE-host run",
 "sha256":hashlib.sha256(exe.read_bytes()).hexdigest(),
 "aex":str(exe),"imports":sorted(imports),
 "AEGP_entry":True,"read_api_contract":needed,
 "private_TDB_BEE_FLT_import":False,"mutation_api_absent":True,
 "arb_value_payload_requested":False,
 "user_host_executed":False}
dst=Path(os.environ.get("CNL_EFFECT_IDENTITY_RECEIPT",r"D:\Developer\ShapeLayerAE\results\cnl_owned_effect_identity_probe_v1_20261012.json"))
dst.parent.mkdir(parents=True,exist_ok=True)
dst.write_text(json.dumps(receipt,indent=2)+"\n")
print("PASS native AEGP read-only source and PE checks")
print("SHA256",receipt["sha256"])
print("SAVED",dst)
