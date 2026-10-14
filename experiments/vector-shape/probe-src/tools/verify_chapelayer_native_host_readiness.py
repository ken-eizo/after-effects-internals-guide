"""ChapeLayer independent-native-layer evidence gate.
Read-only Adobe binary checks and offline CNL tests; never invokes private APIs
or edits the installed After Effects application.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import datetime,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
CHECKS=[
 ("host_attach_object_contract","verify_compitem_native_attach_contract.py"),
 ("public_sdk_register_surface","audit_public_sdk_native_layer_extension.py"),
 ("native_layer_bootstrap_four_family","verify_native_layer_birth_death_registration.py"),
 ("aelib_bee_import_calls","verify_aelib_bee_lifecycle_calls.py"),
 ("aelib_bee_birth_arguments","verify_aelib_bee_birth_argument_gates.py"),
 ("byte_map_not_native_layer_registrar","verify_bee_birth_map_vs_layer_register.py"),
 ("native_layer_bootstrap_nine_family","verify_full_bee_layer_registrar_bootstrap.py"),
 ("ml_plugin_loader_not_bee_provider","verify_pluginsupport_factory_not_bee_owner.py"),
]
def run(name,command):
 started=time.perf_counter()
 try:
  completed=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                           text=True,errors="replace",timeout=180,check=False)
  success=completed.returncode==0
  output=completed.stdout.strip().splitlines()
  return {"check":name,"status":"PASS" if success else "FAIL",
          "exit_code":completed.returncode,
          "elapsed_s":round(time.perf_counter()-started,2),
          "output_tail":output[-8:]}
 except Exception as exc:
  return {"check":name,"status":"FAIL","error":repr(exc),
          "elapsed_s":round(time.perf_counter()-started,2)}
missing=[name for name,s in CHECKS if not (HERE/s).is_file()]
if missing:raise SystemExit("Missing verifier scripts: "+", ".join(missing))
jobs=[(name,[sys.executable,str(HERE/script)]) for name,script in CHECKS]
native=Path(r"D:\Developer\ShapeLayerAE\build\native_shape_layer_prototype")
jobs.append(("cnl_native_timeline_4_ctest",["ctest","--test-dir",str(native),
                                   "-C","Release","--output-on-failure"]))
checks=[]
with ThreadPoolExecutor(max_workers=2) as pool:
 tasks={pool.submit(run,name,cmd):name for name,cmd in jobs}
 for f in as_completed(tasks):
  result=f.result()
  checks.append(result)
  print(result["status"],result["check"],result.get("elapsed_s","?"),"seconds",flush=True)
checks.sort(key=lambda x:x["check"])
all_pass=all(x["status"]=="PASS" for x in checks)
aex=native/"Release"/"CNLNativeShapeLayer.aex"
public_path=ROOT/"datasets"/"ae-public-sdk-native-layer-extension-surface-25-6.json"
public=json.loads(public_path.read_text(encoding="utf-8")) if public_path.exists() else {}
public_register=public.get("register_suite",{})
public_layer_native=(public_register.get("has_custom_layer_class_registration") is True)
public_tdb_native=(public_register.get("has_custom_tdb_stream_type_registration") is True)
report={
 "date":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "scope":"Adobe AE2025/2026 pinned static evidence plus installed SDK25.6 and native CNL offline tests",
 "offline_evidence_gates_pass":all_pass,
 "checks":checks,
 "cnl_AEX_exists":aex.is_file(),
 "cnl_AEX_size_bytes":aex.stat().st_size if aex.is_file() else None,
 "public_sdk_custom_BEE_Layer_registration_found":public_layer_native,
 "public_sdk_custom_TDB_StreamBase_registration_found":public_tdb_native,
 "host_accepted_foreign_BEE_Layer_proven":False,
 "host_owned_native_Contents_editor_proven":False,
 "native_custom_layer_aep_save_reopen_proven":False,
 "native_custom_layer_vectorart_renderer_proven":False,
 "native_custom_layer_unload_lifecycle_proven":False,
 "independent_chapelayer_product_complete":False,
 "decision":"NOT_DEMONSTRATED_HOST_NATIVE_LAYER_ADMISSION" if all_pass else "BASELINE_EVIDENCE_RECHECK_FAILED",
 "note":"PASS means available offline invariants reproduced. It does not prove or disprove all undocumented host extension routes. Positive host-native admission, editor, save/reopen and renderer tests are mandatory before delivery.",
 "no_AE_private_calls":True,
 "no_AE_plugin_installs":True
}
out=ROOT/"datasets"/"chapelayer-native-host-admission-readiness.json"
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("EVIDENCE",str(out))
print("NATIVE HOST ADMISSION",report["decision"])
print("OFFLINE TESTS",len(checks),"of",len(jobs),"passed" if all_pass else "one or more failed")
if not all_pass:raise SystemExit(2)
