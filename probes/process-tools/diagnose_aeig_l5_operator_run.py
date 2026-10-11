from pathlib import Path
import hashlib, json, subprocess, sys
ROOT=Path(r"D:\Developer\After Effects Internals Guide")
RUNS=ROOT/"experiments"/"observatory"/"runs"
TOOLS=ROOT/"probes"/"process-tools"
PKG=ROOT/"experiments"/"user-run"/"AEIG-1.0-L5"
EXPECTED_AEX="DA8693DBD6B7CCC1BBF3043608D4FD7C93557D9CAF3F08A6B78D0BD5B6A1BB0F"
EXPECTED={
 "EXP-CACHE-002":["receipt-matrix.tsv","fixture-script.log","fixture-output-A.avi","fixture-output-B.avi","environment.txt"],
 "EXP-PLUGIN-001":["suite-acquisition.tsv"],
 "EXP-RG-001":["host-trace.log","trace-control.tsv"],
 "EXP-SCRIPT-001":["runtime-reflection.tsv"],
}
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest().upper()
def tail(path,n=12):
    if not path.exists(): return []
    return path.read_text(encoding="utf-8-sig",errors="replace").splitlines()[-n:]
print("AEIG L5 operator-run diagnostics (read-only)")
print("-")
aex=PKG/"plugin"/"AEGP"/"AEIGReceiptArtie.aex"
print("AEX", "present" if aex.exists() else "missing", sha(aex) if aex.exists() else "")
print("AEX expected", EXPECTED_AEX)
rc=subprocess.run([sys.executable,str(TOOLS/"verify_aeig_static_rc.py")],capture_output=True,text=True,encoding="utf-8",errors="replace")
print("Static RC", "PASS" if rc.returncode==0 else "FAIL")
missing=[]
for exp,names in EXPECTED.items():
    base=RUNS/exp
    print(f"[{exp}]")
    for name in names:
        p=base/name
        if p.exists():
            print(f"  OK {name} size={p.stat().st_size}")
        else:
            print(f"  MISSING {name}"); missing.append(f"{exp}/{name}")
fixture=RUNS/"EXP-CACHE-002"/"fixture-script.log"
if fixture.exists():
    print("fixture tail:")
    for line in tail(fixture): print("  "+line)
for exp in EXPECTED:
    mp=ROOT/"experiments"/"observatory"/"manifests"/f"{exp}.json"
    if mp.exists():
        try:
            m=json.loads(mp.read_text(encoding="utf-8-sig")); print(f"manifest {exp}: {m.get('status')}")
        except Exception as e: print(f"manifest {exp}: parse-error {e}")
if missing:
    print("EARLIEST FAILURE CLASS: capture incomplete or operator run not executed")
    print("Missing",len(missing),"required raw artifacts")
    raise SystemExit(2)
print("All required raw artifacts are present. Run 02_VERIFY_RESULTS.cmd / finalizer next.")
raise SystemExit(0)
