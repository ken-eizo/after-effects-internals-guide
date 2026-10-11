from pathlib import Path
import argparse, csv, hashlib, subprocess, sys
from aeig_operator_session import read_kv, evaluate_session
ROOT=Path(r"D:\Developer\After Effects Internals Guide")
ap=argparse.ArgumentParser()
ap.add_argument("--allow-stale-capture",action="store_true",help="safety preflight before archival; still requires AE stopped and probe absent")
args=ap.parse_args()
PKG=ROOT/"experiments"/"user-run"/"AEIG-1.0-L5"
RUNS=ROOT/"experiments"/"observatory"/"runs"
AE=Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe")
DST=Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\Plug-ins\AEIG-Probes\AEIGReceiptArtie.aex")
AEX=PKG/"plugin"/"AEGP"/"AEIGReceiptArtie.aex"
EXPECTED="DA8693DBD6B7CCC1BBF3043608D4FD7C93557D9CAF3F08A6B78D0BD5B6A1BB0F"
DATA=ROOT/"datasets"
SESSION=DATA/"aeig-l5-operator-session.env"
FINGER=DATA/"aeig-static-rc-fingerprint.txt"
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest().upper()
checks=[]
def add(name,ok,detail): checks.append((name,bool(ok),detail))
add('ae-binary',AE.exists(),str(AE))
add('canonical-aex',AEX.exists() and sha(AEX)==EXPECTED,sha(AEX) if AEX.exists() else 'missing')
add('static-rc-manifest',(ROOT/'datasets'/'aeig-static-rc-manifest.csv').exists(),'frozen manifest present')
try:
    task=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,text=True,encoding='utf-8',errors='replace')
    procs=task.stdout.lower()
except Exception as e:
    procs=''; add('process-query',False,type(e).__name__)
for exe in ('afterfx.exe','afterfx.com','aerender.exe'):
    add('not-running:'+exe,exe not in procs,'running' if exe in procs else 'not running')
add('probe-not-installed',not DST.exists(),str(DST))
ver=''
if AE.exists():
    ps=f"(Get-Item -LiteralPath '{AE}').VersionInfo.FileVersion"
    p=subprocess.run(['powershell','-NoProfile','-Command',ps],capture_output=True,text=True,encoding='utf-8',errors='replace')
    ver=p.stdout.strip()
add('ae-version-26.3',ver.startswith('26.3'),ver or 'unavailable')
mutable=[]
for exp,names in {
 'EXP-CACHE-002':['receipt-matrix.tsv','fixture-script.log','fixture-output-A.avi','fixture-output-B.avi','environment.txt'],
 'EXP-PLUGIN-001':['suite-acquisition.tsv'],
 'EXP-RG-001':['host-trace.log','trace-control.tsv','artisan-stage.tsv','current-pass.txt'],
 'EXP-SCRIPT-001':['runtime-reflection.tsv'],
}.items():
    d=RUNS/exp
    mutable += [str(d/n) for n in names if (d/n).exists()]
add('no-unarchived-user-capture',args.allow_stale_capture or not mutable,f"stale={len(mutable)}" + (' (allowed before archive)' if args.allow_stale_capture and mutable else ''))
if not args.allow_stale_capture:
    sv=read_kv(SESSION); current=FINGER.read_text(encoding="utf-8-sig",errors="replace").strip() if FINGER.exists() else ""
    se=evaluate_session(sv,current,EXPECTED); session_ok=SESSION.exists() and se["ok"]
    add('operator-session-issued',session_ok,f"session={se['session_id'] or 'missing'} fingerprint={se['fingerprint'] or 'missing'} errors={se['errors']}")
v=subprocess.run([sys.executable,str(ROOT/'probes'/'process-tools'/'verify_aeig_static_rc.py')],capture_output=True,text=True,encoding='utf-8',errors='replace')
add('static-rc-verification',v.returncode==0,(v.stdout+v.stderr).strip().replace('\n',' | '))
for name,ok,detail in checks:
    print(('PASS' if ok else 'BLOCK')+'\t'+name+'\t'+detail)
if mutable:
    print('STALE_CAPTURE_FILES')
    for p in mutable: print(p)
blocked=[c for c in checks if not c[1]]
print(f'AEIG L5 OPERATOR PREFLIGHT: {"PASS" if not blocked else "BLOCKED"} ({len(blocked)} blocker(s))')
raise SystemExit(0 if not blocked else 2)
