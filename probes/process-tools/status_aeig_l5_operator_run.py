from pathlib import Path
import csv, json, subprocess
from aeig_operator_session import read_kv, evaluate_session

ROOT = Path(r"D:\Developer\After Effects Internals Guide")
RUNS = ROOT / "experiments" / "observatory" / "runs"
DATA = ROOT / "datasets"
DST = Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\Plug-ins\AEIG-Probes\AEIGReceiptArtie.aex")
EXPECTED_AEX="DA8693DBD6B7CCC1BBF3043608D4FD7C93557D9CAF3F08A6B78D0BD5B6A1BB0F"

def exists(exp, name):
    return (RUNS / exp / name).exists()

def proc(name):
    p = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {name}"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return name.lower() in p.stdout.lower()

def read_json(path):
    try: return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception: return {}

def read_decisions(path):
    if not path.exists(): return []
    with path.open(encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))

def truth(v): return str(v).lower() in {"true","1","yes"}
verification_path = DATA / "aeig-l5-user-run-verification.json"
decisions_path = DATA / "aeig-l5-domain-decisions.csv"
session_path=DATA/"aeig-l5-operator-session.env"
session=read_kv(session_path)
finger_path=DATA/"aeig-static-rc-fingerprint.txt"
current_finger=finger_path.read_text(encoding="utf-8-sig",errors="replace").strip() if finger_path.exists() else ""
session_eval=evaluate_session(session,current_finger,EXPECTED_AEX)
session_valid=session_path.exists() and session_eval["ok"]
verification = read_json(verification_path) if verification_path.exists() else {}
decisions = read_decisions(decisions_path)
state = {
    "afterfx": proc("AfterFX.exe"), "afterfx_com": proc("AfterFX.com"), "aerender": proc("aerender.exe"),
    "probe_installed": DST.exists(),
    "receipt": exists("EXP-CACHE-002", "receipt-matrix.tsv"),
    "fixture_log": exists("EXP-CACHE-002", "fixture-script.log"),
    "output_a": exists("EXP-CACHE-002", "fixture-output-A.avi"),
    "output_b": exists("EXP-CACHE-002", "fixture-output-B.avi"),
    "suite_matrix": exists("EXP-PLUGIN-001", "suite-acquisition.tsv"),
    "rg_trace": exists("EXP-RG-001", "host-trace.log"),
    "trace_control": exists("EXP-RG-001", "trace-control.tsv"),
    "current_pass": exists("EXP-RG-001", "current-pass.txt"),
    "environment": exists("EXP-CACHE-002", "environment.txt"),
    "reflection": exists("EXP-SCRIPT-001", "runtime-reflection.tsv"),
    "verification_present": verification_path.exists(),
    "verification_capture_complete": bool(verification.get("capture_complete", False)),
    "domain_decisions_present": decisions_path.exists(),
    "operator_session_present": session_path.exists(),
    "operator_session_id": session.get("session_id",""),
    "operator_session_valid": session_valid,
}
pass_path=RUNS/"EXP-RG-001"/"current-pass.txt"
state["current_pass_done"]=pass_path.exists() and pass_path.read_text(encoding="utf-8-sig",errors="replace").strip()=="DONE"
raw_keys=("receipt","fixture_log","output_a","output_b","suite_matrix","rg_trace","trace_control","current_pass","environment","reflection")
raw=[state[k] for k in raw_keys]
core={r.get("domain"):r for r in decisions}
decision_complete=(set(core)=={"state-identity","cache","render-graph","plugin-host"})
all_evidence=decision_complete and all(truth(r.get("evidence_ready")) for r in core.values())
revision_due=decision_complete and any(truth(r.get("model_revision_required")) for r in core.values())

if any(raw) and not session_valid:
    phase = "CAPTURE_SESSION_INVALID"
elif state["verification_capture_complete"] and decision_complete:
    phase = "FINALIZED_PROMOTABLE" if all_evidence and not revision_due else "FINALIZED_REVIEW_REQUIRED"
elif all(raw) and state["current_pass_done"]: phase = "CAPTURE_COMPLETE_VERIFY_PENDING"
elif all(raw): phase = "CAPTURE_RAW_PRESENT_NOT_DONE"
elif any(raw): phase = "CAPTURE_PARTIAL"
elif state["probe_installed"] and state["afterfx"]: phase = "AE_RUNNING_WITH_PROBE"
elif state["probe_installed"]: phase = "PROBE_INSTALLED_AE_STOPPED"
elif state["afterfx"] or state["afterfx_com"] or state["aerender"]: phase = "AE_PROCESS_ACTIVE_NO_PROBE"
elif session_valid: phase = "READY_NOT_STARTED"
else: phase = "NEEDS_PREPARE"

payload={"phase":phase, **state, "all_domain_evidence_ready":all_evidence,
         "model_revision_required":revision_due, "raw_artifacts_present":sum(raw), "raw_artifacts_required":len(raw_keys)}
print("AEIG L5 operator phase:", phase)
for key,value in payload.items():
    if key != "phase": print(f"{key}={value}")
out=DATA/"aeig-l5-operator-status.json"
out.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
print("wrote",out)
