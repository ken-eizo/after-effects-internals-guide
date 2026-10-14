"""Native Timeline product acceptance gate audit (read-only).
0 exit code means the audit completed, NOT the requested native plug-in is done.
"""
from pathlib import Path
import json,hashlib,pefile
root=Path(__file__).resolve().parents[4]
aud=json.loads((root/"datasets"/"ae25_6_public_native_stream_provider_api_scope_audit.json").read_text(encoding="utf-8"))
paint=json.loads((root/"datasets"/"ae-paint-native-hierarchy-host-v2-2026-20261014-summary.json").read_text(encoding="utf-8"))
lab=Path(r"D:\Developer\ShapeLayerAE\labs\native_shape_layer_prototype")
source=(lab/"ChapeTimelineHostDemo.cpp").read_text(encoding="utf-8")
aex=Path(r"D:\Developer\ShapeLayerAE\build\native_shape_layer_prototype\Release\CNLNativeShapeLayer.aex")
assert aex.exists()
pe=pefile.PE(str(aex))
assert pe.FILE_HEADER.Machine==0x8664
imports={d.dll.decode(errors="replace").lower() for d in pe.DIRECTORY_ENTRY_IMPORT}
assert "bee.dll" not in imports and "tdb.dll" not in imports
assert "adobe_layer_registered" in source and "adobe_contents_registered" in source
assert paint["native_stream_node_count"]==170
assert aud["scanned_header_count"]==70
requirements={
 "plugin_is_a_valid_aex":True,
 "c_cpp_native_engine_and_selftest_available":True,
 "can_read_existing_adobe_paint_native_streams":True,
 "foreign_native_stream_provider_sdk_available":False,
 "can_register_new_ae_host_native_stream_class":False,
 "can_register_foreign_named_indexed_parent_schema":False,
 "can_attach_custom_stream_to_ae_standard_timeline":False,
 "custom_native_stream_can_be_keyframed_in_ae":False,
 "custom_native_stream_aep_save_reopen":False,
 "custom_native_stream_undo_redo":False,
 "custom_native_stream_live_host_lifecycle":False,
 "custom_native_stream_macos_test":False
}
acceptance_keys=list(requirements)[3:]
status="PASS" if all(requirements[k] for k in acceptance_keys) else "NOT_DELIVERED_HOST_NATIVE_CUSTOM_STREAM"
payload={
 "date":"2026-10-14",
 "audit_status":"PASS",
 "product_acceptance":status,
 "user_requested_output":"An AEX that makes newly defined third-party native property groups and leaf classes appear directly in Adobe's standard Timeline",
 "criteria":requirements,
 "aex_sha256":hashlib.sha256(aex.read_bytes()).hexdigest(),
 "reliability_warning":"A working CNL-owned engine, read-only Paint metadata, or can-add over existing Adobe types must never be reported as host-native new type registration.",
 "host_ae_mutated_by_this_test":False
}
out=root/"datasets"/"chape_host_native_timeline_product_gate_20261014.json"
out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("Audit PASS: Windows AEX exists and x64 PE is valid; native Paint inspection confirmed")
print("Product status:",status)
for k,v in requirements.items():print("  ",("PASS" if v else "NOT_MET"),k)
print("Record:",out)
