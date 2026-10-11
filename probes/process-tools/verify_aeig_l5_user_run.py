from pathlib import Path
import subprocess, sys, hashlib, json, re
from aeig_operator_session import read_kv, evaluate_session, evaluate_raw_times

ROOT=Path(r"D:\Developer\After Effects Internals Guide")
DATA=ROOT/"datasets"
TOOLS=ROOT/"probes"/"process-tools"
RUNS=ROOT/"experiments"/"observatory"/"runs"
CACHE=RUNS/"EXP-CACHE-002"
PLUGIN=RUNS/"EXP-PLUGIN-001"
RG=RUNS/"EXP-RG-001"
SCRIPT=RUNS/"EXP-SCRIPT-001"
OUT=DATA/"aeig-l5-user-run-verification.json"
SESSION=DATA/"aeig-l5-operator-session.env"
FINGER=DATA/"aeig-static-rc-fingerprint.txt"
EXPECTED_AEX="DA8693DBD6B7CCC1BBF3043608D4FD7C93557D9CAF3F08A6B78D0BD5B6A1BB0F"

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest().upper()

def run(script):
    p=subprocess.run([sys.executable,str(TOOLS/script)],capture_output=True,text=True,
                     encoding="utf-8",errors="replace")
    print(f"[{script}] exit={p.returncode}")
    if p.stdout: print(p.stdout.rstrip())
    if p.stderr: print(p.stderr.rstrip(),file=sys.stderr)
    return {"exit":p.returncode,"stdout":p.stdout,"stderr":p.stderr}

results={}
session_values=read_kv(SESSION)
current_fingerprint=FINGER.read_text(encoding="utf-8-sig",errors="replace").strip() if FINGER.exists() else ""
session_eval=evaluate_session(session_values,current_fingerprint,EXPECTED_AEX)
issued_ms=session_eval["issued_unix_ms"]
results["session"]={"exists":SESSION.exists(),**session_eval}
results["receipt_analysis"]=run("analyze_receipt_experiment.py")
results["plugin_analysis"]=run("analyze_plugin_host_experiment.py")
results["rg_analysis"]=run("analyze_rg_trace_experiment.py")
results["script_analysis"]=run("analyze_scripting_reflection.py")
aex=ROOT/"experiments"/"user-run"/"AEIG-1.0-L5"/"plugin"/"AEGP"/"AEIGReceiptArtie.aex"
results["aex"]={"exists":aex.exists(),"sha256":sha(aex) if aex.exists() else ""}
results["aex"]["matches_expected"]=results["aex"]["sha256"]==EXPECTED_AEX

for label,name in (("A","fixture-output-A.avi"),("B","fixture-output-B.avi")):
    p=CACHE/name
    results[f"output_{label}"]={
        "exists":p.exists(),
        "size":p.stat().st_size if p.exists() else 0,
        "sha256":sha(p) if p.exists() else "",
    }
results["output_pair_materialized"]=all(
    results[f"output_{label}"]["exists"] and results[f"output_{label}"]["size"]>0
    for label in ("A","B")
)
results["outputs_differ"]=(results["output_pair_materialized"] and
    results["output_A"]["sha256"] != results["output_B"]["sha256"])

fixture=CACHE/"fixture-script.log"
text=fixture.read_text(encoding="utf-8-sig",errors="replace") if fixture.exists() else ""
initial_blur=re.search(r"fx1=ADBE Gaussian Blur 2 blur=([-+0-9.eE]+)",text)
mutation_blur=re.search(r"MUTATION blur=([-+0-9.eE]+)",text)
results["fixture"]={
    "exists":fixture.exists(),
    "renderer":"renderer=AEIG Receipt Probe" in text,
    "three_d":"threeDLayer=true" in text,
    "three_effects":"numEffects=3" in text,
    "pass_a":"PASS_END=A" in text,
    "initial_blur_10":bool(initial_blur and abs(float(initial_blur.group(1))-10.0)<1e-9),
    "mutation_blur_75":bool(mutation_blur and abs(float(mutation_blur.group(1))-75.0)<1e-9),
    "pass_b":"PASS_END=B" in text,
    "script_exit":"SCRIPT_EXIT" in text,
    "no_script_error":"\tERR=" not in text,
}
env=CACHE/"environment.txt"
env_text=env.read_text(encoding="utf-8-sig",errors="replace") if env.exists() else ""
env_values=read_kv(env)
results["environment"]={
    "exists":env.exists(),
    "ae_version":env_values.get("app.version",""),
    "build_number":env_values.get("app.buildNumber",""),
    "os":env_values.get("os",""),
    "ae_26_3":env_values.get("app.version","").startswith("26.3"),
    "build_number_present":bool(env_values.get("app.buildNumber","")),
    "os_present":bool(env_values.get("os","")),
    "session_id_matches":bool(results["session"]["session_id"] and env_values.get("aeig.session_id")==results["session"]["session_id"]),
    "session_fingerprint_matches":bool(results["session"]["fingerprint"] and env_values.get("aeig.static_rc_fingerprint")==results["session"]["fingerprint"]),
    "session_issued_matches":str(issued_ms)==env_values.get("aeig.issued_unix_ms",""),
    "session_aex_matches":env_values.get("aeig.canonical_aex_sha256","")==EXPECTED_AEX,
}
raw_paths={
 "receipt":CACHE/"receipt-matrix.tsv", "fixture":CACHE/"fixture-script.log",
 "output_a":CACHE/"fixture-output-A.avi", "output_b":CACHE/"fixture-output-B.avi",
 "environment":CACHE/"environment.txt", "suite":PLUGIN/"suite-acquisition.tsv",
 "trace":RG/"host-trace.log", "trace_control":RG/"trace-control.tsv",
 "current_pass":RG/"current-pass.txt", "reflection":SCRIPT/"runtime-reflection.tsv",
}
results["raw_session_time"]=evaluate_raw_times(raw_paths,issued_ms,2000)
passfile=RG/"current-pass.txt"
results["current_pass_done"]=passfile.exists() and passfile.read_text(encoding="utf-8-sig",errors="replace").strip()=="DONE"
results["fixture_session_matches"]=bool(results["session"]["session_id"] and f"SESSION_ID={results['session']['session_id']} RC={results['session']['fingerprint']} ISSUED={issued_ms}" in text)
analysis_ok=all(results[k]["exit"]==0 for k in (
    "receipt_analysis","plugin_analysis","rg_analysis","script_analysis"))
results["capture_complete"]=all([
    analysis_ok,
    results["aex"]["matches_expected"],
    all(results["fixture"].values()),
    results["session"]["exists"] and results["session"]["ok"],
    results["fixture_session_matches"], results["raw_session_time"]["all_after_issue"], results["current_pass_done"],
    results["environment"]["exists"], results["environment"]["ae_26_3"],
    results["environment"]["build_number_present"], results["environment"]["os_present"],
    results["environment"]["session_id_matches"], results["environment"]["session_fingerprint_matches"],
    results["environment"]["session_issued_matches"], results["environment"]["session_aex_matches"],
    results["output_pair_materialized"],
])
results["semantic_checks"]={
    "outputs_differ":results["outputs_differ"],
}
results["semantic_checks_passed"]=all(results["semantic_checks"].values())
results["all_required_checks_passed"]=(
    results["capture_complete"] and results["semantic_checks_passed"]
)
OUT.write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("AEX hash",results["aex"]["sha256"],"expected",results["aex"]["matches_expected"])
print("capture complete",results["capture_complete"])
print("outputs materialized",results["output_pair_materialized"],"differ",results["outputs_differ"])
print("fixture",results["fixture"])
print("session",results["session"],"fixture_session_matches",results["fixture_session_matches"],"raw_after_issue",results["raw_session_time"]["all_after_issue"],"current_pass_done",results["current_pass_done"])
print("environment",results["environment"])
state="PASS" if results["all_required_checks_passed"] else (
    "CAPTURED_WITH_SEMANTIC_GATE_FAILURE" if results["capture_complete"] else "INCOMPLETE")
print("AEIG L5 USER RUN:",state)
print("wrote",OUT)
raise SystemExit(0 if results["all_required_checks_passed"] else 2)