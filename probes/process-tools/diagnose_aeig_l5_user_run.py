from pathlib import Path
import json, re
from aeig_operator_session import read_kv, evaluate_session, evaluate_raw_times
ROOT=Path(r"D:\Developer\After Effects Internals Guide")
RUNS=ROOT/"experiments"/"observatory"/"runs"
DATA=ROOT/"datasets"
EXPECTED_AEX="DA8693DBD6B7CCC1BBF3043608D4FD7C93557D9CAF3F08A6B78D0BD5B6A1BB0F"
checks={
 "session":DATA/"aeig-l5-operator-session.env",
 "fixture_log":RUNS/"EXP-CACHE-002"/"fixture-script.log",
 "receipt":RUNS/"EXP-CACHE-002"/"receipt-matrix.tsv",
 "output_A":RUNS/"EXP-CACHE-002"/"fixture-output-A.avi",
 "output_B":RUNS/"EXP-CACHE-002"/"fixture-output-B.avi",
 "suite":RUNS/"EXP-PLUGIN-001"/"suite-acquisition.tsv",
 "trace":RUNS/"EXP-RG-001"/"host-trace.log",
 "trace_control":RUNS/"EXP-RG-001"/"trace-control.tsv",
 "current_pass":RUNS/"EXP-RG-001"/"current-pass.txt",
 "reflection":RUNS/"EXP-SCRIPT-001"/"runtime-reflection.tsv",
 "environment":RUNS/"EXP-CACHE-002"/"environment.txt",
}
state={k:{"exists":p.exists(),"bytes":p.stat().st_size if p.exists() else 0} for k,p in checks.items()}
issues=[]
session=read_kv(checks["session"])
finger_path=DATA/"aeig-static-rc-fingerprint.txt"
current_finger=finger_path.read_text(encoding="utf-8-sig",errors="replace").strip() if finger_path.exists() else ""
session_eval=evaluate_session(session,current_finger,EXPECTED_AEX)
if not checks["session"].exists() or not session_eval["ok"]: issues.append("operator session metadata invalid: "+",".join(session_eval["errors"]))
if not state["fixture_log"]["exists"]: issues.append("JSX did not start or could not write fixture log")
if state["fixture_log"]["exists"]:
    text=checks["fixture_log"].read_text(encoding="utf-8-sig",errors="replace")
    if "SCRIPT_ENTER" not in text: issues.append("fixture log exists but SCRIPT_ENTER is missing")
    sid=session.get("session_id","")
    if sid and ("SESSION_ID="+sid) not in text: issues.append("fixture log session ID does not match prepared session")
    expected_stamp=f"SESSION_ID={sid} RC={session_eval['fingerprint']} ISSUED={session_eval['issued_unix_ms']}" if sid else ""
    if expected_stamp and expected_stamp not in text: issues.append("fixture log session fingerprint/issued metadata does not match prepared session")
    if "renderer=AEIG Receipt Probe" not in text: issues.append("AEIG Receipt Probe renderer was not selected")
    if "PASS_END=A" not in text: issues.append("pass A did not finish")
    initial=re.search(r"fx1=ADBE Gaussian Blur 2 blur=([-+0-9.eE]+)",text); mutated=re.search(r"MUTATION blur=([-+0-9.eE]+)",text)
    if not initial or abs(float(initial.group(1))-10.0)>1e-9: issues.append("Blur=10 initial read-back is missing or incorrect")
    if not mutated or abs(float(mutated.group(1))-75.0)>1e-9: issues.append("Blur=75 mutation read-back is missing or incorrect")
    if "PASS_END=B" not in text: issues.append("pass B did not finish")
    if "SCRIPT_EXIT" not in text: issues.append("script did not reach normal exit")
    for line in text.splitlines():
        if "\tERR=" in line:
            issues.append("fixture script error: "+line.split("\tERR=",1)[1])
for k in ("receipt","suite","trace","trace_control","current_pass","reflection","environment","session"):
    if not state[k]["exists"]: issues.append(f"missing capture: {k}")
for k in ("output_A","output_B"):
    if not state[k]["exists"]: issues.append(f"missing rendered output: {k}")
    elif state[k]["bytes"]<=0: issues.append(f"rendered output is empty: {k}")
raw_time=evaluate_raw_times({k:p for k,p in checks.items() if k!="session"},session_eval["issued_unix_ms"],2000)
stale=[k for k,v in raw_time.get("files",{}).items() if v.get("exists") and not v.get("after_session_issue")]
if session_eval["issued_unix_ms"]>0 and stale: issues.append("raw artifacts predate the prepared operator session: "+",".join(stale))
if checks["current_pass"].exists() and checks["current_pass"].read_text(encoding="utf-8-sig",errors="replace").strip()!="DONE": issues.append("current-pass marker did not reach DONE")
env=read_kv(checks["environment"])
if session_eval["session_id"] and env.get("aeig.session_id")!=session_eval["session_id"]: issues.append("environment session ID does not match prepared session")
if session_eval["fingerprint"] and env.get("aeig.static_rc_fingerprint")!=session_eval["fingerprint"]: issues.append("environment Static RC fingerprint does not match prepared session")
if str(session_eval["issued_unix_ms"])!=env.get("aeig.issued_unix_ms",""): issues.append("environment session issued time does not match prepared session")
if env.get("aeig.canonical_aex_sha256")!=EXPECTED_AEX: issues.append("environment canonical AEX hash does not match")
summary={"checks":state,"session":session_eval,"raw_session_time":raw_time,"issues":issues,"status":"PASS" if not issues else "INCOMPLETE"}
out=DATA/"aeig-l5-user-run-diagnostic.json"
out.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("AEIG L5 diagnostic:",summary["status"])
for issue in issues: print("-",issue)
print("wrote",out)
raise SystemExit(0 if not issues else 2)
