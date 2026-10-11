"""Cross-check independently recovered native required TDB stream methods.

Only tests the persistent, readable AEIG JSON evidence derived from exact DLLs.
"""
from pathlib import Path
import json
root=Path(r"D:\Developer\After Effects Internals Guide\datasets")
reg=json.loads((root/"ae-native-stream-private-registration-lifetime-2025-2026.json").read_text(encoding="utf-8"))
vt=json.loads((root/"ae-tdb-stream-vtable-creator-required-methods-2025-2026.json").read_text(encoding="utf-8"))
verified={}
for year in ("2025","2026"):
 r=reg["versions"][year]
 v=vt["versions"][year]["tables"]
 assert r["registration_eager_CreateStream_sites"]
 assert r["create_stream_invokes_std_function_via_virt_slot_0x10"]
 assert r["register_factory_clones_std_function_via_virt_slot0"]
 assert r["register_factory_destroys_temporary_std_function_via_virt_slot_0x20"]
 assert r["sc_registration_wrapper_destructor_calls_unregister_all"] is False
 assert r["explicit_unregister_all_reverse_iteration"]
 assert r["unregister_all_unlinks_names"]
 assert r["factory_unregister_native_destructor_virtual_call"]
 expected={
 "TDB_StreamBase":{
 "0x58":"?IsLeaf@TDB_StreamBase@@",
 "0x80":"?GetAsLeaf@TDB_StreamBase@@",
 "0x150":"?SetupCanonicalLayout@TDB_StreamBase@@"},
 "TDB_Stream":{
 "0x58":"?IsLeaf@TDB_Stream@@",
 "0x80":"?GetAsLeaf@TDB_Stream@@",
 "0x298":"?IsSeparationLeader@TDB_Stream@@",
 "0x190":"?InsertDefaultKey@TDB_Stream@@"},
 "TDB_StreamGroup":{"0x150":"?SetupCanonicalLayout@TDB_StreamGroup@@"}}
 for classname,slots in expected.items():
  for off,sym in slots.items():
   record=v[classname]["slots"][off]
   assert record["target_executable"],(year,classname,off,record)
   assert record["exported_symbol"].startswith(sym),(year,classname,off,record)
 verified[year]={
 "creator_callback_is_C++_std_function_erasure":True,
 "registration_sync_creates_stream":True,
 "stream_creator_invoked_at_std_function_virtual_offset":"0x10",
 "TDB_StreamBase_IsLeaf_virtual_offset":"0x58",
 "TDB_StreamBase_GetAsLeaf_virtual_offset":"0x80",
 "TDB_StreamBase_SetupCanonicalLayout_virtual_offset":"0x150",
 "TDB_Stream_IsSeparationLeader_virtual_offset":"0x298",
 "helper_unregister_in_reverse_order":True,
 "helper_destructor_does_not_automatically_unregister":True,
 "external_plugin_type_registered":False
 }
 print("PASS",year,"TDB callback lifecycle and exact named StreamBase/Stream vtable methods")
receipt=root/"ae-native-registration-required-methods-crosscheck-2025-2026.json"
receipt.write_text(json.dumps({"classification":"E2-L cross-validation independent disassembly paths, not external plugin proof",
"versions":verified},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",receipt)
