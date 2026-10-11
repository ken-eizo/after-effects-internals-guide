"""Verify AE's BEE_StreamSpec -> BEE_Layer + IDPath adapter in two PE builds.
Static only. It does not construct an Adobe object or call BEE APIs.
"""
import json
from pathlib import Path
p=Path(r"D:\Developer\ShapeLayerAE\results\native_streamspec_resolver_effect_gate_2025_2026.json")
raw=json.loads(p.read_text(encoding="utf8"))["versions"]
out={}
expected=[
"mov r8, rdx",
"lea rdx, [rcx + 0x10]",
"mov rcx, qword ptr [rcx + 8]"]
for ver in ("2025","2026"):
 methods=raw[ver]["methods"]
 get=next(x for x in methods if x["symbol"].startswith("?BEE_GetStreamWithSpec@@"))
 has=next(x for x in methods if x["symbol"].startswith("?BEE_StreamTypeHasStream@@"))
 assert len(get["thunks"])==1,(ver,get["thunks"])
 prefix=get["thunks"][0]["prefix"]
 assert prefix[:3]==expected,(ver,prefix)
 assert prefix[3].startswith("jmp 0x"),(ver,prefix)
 assert get["has_pdata"],(ver,"resolver must have full body")
 assert any("call"==i[1] and "qword ptr" in i[2] for i in get["initial_instructions"])
 assert any(i[1]=="call" and "[rax + 0x80]" in i[2] for i in get["initial_instructions"])
 assert any("BEE_IsEffectStreamPath@@" in b["symbol"] for b in has["branches"])
 out[ver]={"BEE_sha256":raw[ver]["BEE_sha256"],
           "adapter_export":get["export_entry"],
           "adapter_real_body":get["resolved_entry"],
           "layer_pointer_byte_offset":8,"stream_id_path_byte_offset":16,
           "third_parameter_redirected_to_output_pointer":True,
           "effect_path_special_case_in_stream_type_test":True,
           "editable_foreign_owner_supported":False}
 print("PASS",ver,"BEE_StreamSpec owner+path adapter and special Effect path branch")
dst=p.parent/"native_streamspec_owner_identity_verified_2025_2026.json"
dst.write_text(json.dumps({"classification":"cross-version static machine code; not host extension API",
"versions":out},indent=2)+"\n",encoding="utf8")
print("SAVED",dst)
