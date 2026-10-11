from pathlib import Path
from datetime import date, datetime, timezone
import argparse, csv, hashlib, json, shutil, subprocess, sys, time

ROOT=Path(r"D:\Developer\After Effects Internals Guide")
TOOLS=ROOT/"probes"/"process-tools"; DATA=ROOT/"datasets"; DOCS=ROOT/"docs"/"reference"
ap=argparse.ArgumentParser(); ap.add_argument("--mode",choices=("success","refute-pred004"),default="success"); args=ap.parse_args()
MODE=args.mode; REFUTE_PRED004=MODE=="refute-pred004"
CLONE=ROOT/"scratch"/("finalizer-refutation-selftest" if REFUTE_PRED004 else "finalizer-success-selftest")
OUT=DATA/("aeig-finalizer-refutation-selftest.json" if REFUTE_PRED004 else "aeig-finalizer-success-selftest.json")
PAGE=DOCS/("finalizer-refutation-selftest.md" if REFUTE_PRED004 else "finalizer-success-selftest.md")
EXPECTED_AEX="DA8693DBD6B7CCC1BBF3043608D4FD7C93557D9CAF3F08A6B78D0BD5B6A1BB0F"

def digest(p):
    if not p.exists(): return "MISSING"
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def run(root,name):
    return subprocess.run([sys.executable,str(root/"probes"/"process-tools"/name)],cwd=str(root),
        capture_output=True,text=True,encoding="utf-8",errors="replace")

def rows(p):
    with p.open(encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))

def write(path,text,mode="w"):
    path.parent.mkdir(parents=True,exist_ok=True); path.open(mode,encoding="utf-8",newline="").write(text)
protected=[DATA/"aeig-prediction-log.csv",DATA/"aeig-l5-domain-decisions.csv",DATA/"aeig-domain-coverage.csv",
           DATA/"aeig-static-rc-manifest.csv",DATA/"aeig-static-rc-fingerprint.txt",ROOT/"README.md",ROOT/"docs"/"index.md",
           ROOT/"VERSION",DOCS/"aeig-1.0-release.md"]
for exp in ("EXP-CACHE-002","EXP-PLUGIN-001","EXP-RG-001","EXP-SCRIPT-001"):
    protected.append(ROOT/"experiments"/"observatory"/"manifests"/f"{exp}.json")
source_before={str(p):digest(p) for p in protected}

if CLONE.exists(): shutil.rmtree(CLONE)
(CLONE/"datasets").mkdir(parents=True)
shutil.copytree(ROOT/"docs",CLONE/"docs")
for p in DATA.iterdir():
    if p.is_file(): shutil.copy2(p,CLONE/"datasets"/p.name)
shutil.copytree(TOOLS,CLONE/"probes"/"process-tools")
shutil.copytree(ROOT/"experiments"/"user-run",CLONE/"experiments"/"user-run")
shutil.copytree(ROOT/"experiments"/"observatory"/"manifests",
                CLONE/"experiments"/"observatory"/"manifests")
for exp_doc in (ROOT/"experiments").glob("*.md"):
    shutil.copy2(exp_doc,CLONE/"experiments"/exp_doc.name)
if (ROOT/"research"/"findings").exists():
    shutil.copytree(ROOT/"research"/"findings",CLONE/"research"/"findings")
(CLONE/"research").mkdir(parents=True,exist_ok=True)
shutil.copy2(ROOT/"research"/"bug-quirks.csv",CLONE/"research"/"bug-quirks.csv")
(CLONE/".github"/"workflows").mkdir(parents=True,exist_ok=True)
shutil.copy2(ROOT/".github"/"workflows"/"docs.yml",CLONE/".github"/"workflows"/"docs.yml")
for name in ("README.md","ROADMAP.md","mkdocs.yml","requirements-docs.txt"):
    shutil.copy2(ROOT/name,CLONE/name)

old1=str(ROOT); old2=old1.replace("\\","\\\\")
new1=str(CLONE); new2=new1.replace("\\","\\\\")
for p in (CLONE/"probes"/"process-tools").glob("*.py"):
    text=p.read_text(encoding="utf-8-sig",errors="replace")
    p.write_text(text.replace(old2,new2).replace(old1,new1),encoding="utf-8")
setup=[]
for name in ("freeze_aeig_static_rc.py","compute_static_rc_fingerprint.py","verify_aeig_static_rc.py"):
    p=run(CLONE,name); setup.append((name,p.returncode,(p.stdout+p.stderr)[-1500:]))
    if p.returncode: break
if len(setup)!=3 or any(code for _,code,_ in setup):
    print("finalizer selftest setup failed",setup); raise SystemExit(2)

fp=(CLONE/"datasets"/"aeig-static-rc-fingerprint.txt").read_text(encoding="utf-8-sig").strip()
aex=CLONE/"experiments"/"user-run"/"AEIG-1.0-L5"/"plugin"/"AEGP"/"AEIGReceiptArtie.aex"
aex_hash=hashlib.sha256(aex.read_bytes()).hexdigest().upper()
issued=int(time.time()*1000)-1000; sid="SYNTH-"+str(issued)
session="\n".join([
    "schema=AEIG-L5-SESSION-v1",f"session_id={sid}",
    f"issued_utc={datetime.now(timezone.utc).isoformat()}",f"issued_unix_ms={issued}",
    f"static_rc_fingerprint={fp}",f"canonical_aex_sha256={aex_hash}",""])
write(CLONE/"datasets"/"aeig-l5-operator-session.env",session)

runs=CLONE/"experiments"/"observatory"/"runs"
cache=runs/"EXP-CACHE-002"; plugin=runs/"EXP-PLUGIN-001"
rg=runs/"EXP-RG-001"; script=runs/"EXP-SCRIPT-001"
for d in (cache,plugin,rg,script): d.mkdir(parents=True,exist_ok=True)
receipt=[]
vals=(-1,0,1,2,3)
for run_pass in ("A","B"):
    for g in vals:
        for n in vals:
            for geom in (0,1):
                gg=3 if g==-1 else g; nn=3 if n==-1 else n
                status=1 if gg>=nn else 2
                if REFUTE_PRED004 and g==0 and n==1 and geom==0: status=1
                receipt.append(f"1\t{run_pass}\tCHECK\t3\t{g}\t{n}\t{geom}\t{status}\t0")
write(cache/"receipt-matrix.tsv","\n".join(receipt)+"\n")

fixture=[f"0\tSESSION_ID={sid} RC={fp} ISSUED={issued}","0\tSCRIPT_ENTER AE=26.3.0",
         "0\trenderer=AEIG Receipt Probe","0\tthreeDLayer=true","0\tfx1=ADBE Gaussian Blur 2 blur=10",
         "0\tnumEffects=3","0\tPASS_END=A status=1","0\tMUTATION blur=75",
         "0\tPASS_END=B status=1","0\tSCRIPT_EXIT"]
write(cache/"fixture-script.log","\n".join(fixture)+"\n")
(cache/"fixture-output-A.avi").write_bytes(b"AEIG-A\x00\x01")
(cache/"fixture-output-B.avi").write_bytes(b"AEIG-B\x00\x02")
env="\n".join(["app.version=26.3.0","app.buildNumber=synthetic-1","os=Windows 10",
    f"aeig.session_id={sid}",f"aeig.static_rc_fingerprint={fp}",f"aeig.issued_unix_ms={issued}",
    f"aeig.canonical_aex_sha256={aex_hash}",""])
write(cache/"environment.txt",env)
with (CLONE/"datasets"/"ae-sdk-25.6-suite-names.csv").open(encoding="utf-8",newline="") as f:
    labels=sorted({r["suite_macro"].removeprefix("k") for r in csv.DictReader(f)})
plines=[]
for i,label in enumerate(labels):
    accepted=1 if i%2==0 else 2
    for selector in range(1,33):
        ok=selector==accepted; err=0 if ok else 1; ptr="0x1" if ok else "0"
        plines.append(f"1\t26\t3\t{label}\t{label}\t{selector}\t{err}\t{ptr}")
write(plugin/"suite-acquisition.tsv","\n".join(plines)+"\n")

cats=["BEE_Eval","BEE_Cache","BEE_CacheLog","BEE_WorkQueue","MixHashGuid",
      "RenderNode.RG_CacheNodeBase","RenderNode.RG_XformNode","TDB_StreamBase","DiskCache"]
trace=[]; control=[]
for seq,run_pass in ((1,"A"),(2,"B")):
    trace.append(f"AEIG_TRACE_BEGIN\tseq={seq}\tpass={run_pass}\tpid=1")
    for j,cat in enumerate(cats): trace.append(f"TRACE\t{cat}\tvalue={run_pass}-{j}")
    trace.append(f"AEIG_TRACE_END\tseq={seq}\tpass={run_pass}\tpid=1")
    control += [f"1\t{seq}\t{run_pass}\tBEGIN\t-\t1",f"1\t{seq}\t{run_pass}\tEND\t-\t1"]
write(rg/"host-trace.log","\n".join(trace)+"\n")
write(rg/"trace-control.tsv","\n".join(control)+"\n")
write(rg/"current-pass.txt","DONE")
rlabels=["Application","Project","CompItem","AVLayer","RenderQueue","RenderQueueItem","OutputModule"]
reflection=["label\tkind\tname\ttype\tdataType\tisReadOnly"]
reflection += [f"{label}\tproperty\tname\treadwrite\tstring\tfalse" for label in rlabels]
write(script/"runtime-reflection.tsv","\n".join(reflection)+"\n")

time.sleep(0.05)
pipeline=run(CLONE,"complete_aeig_1_0_after_operator_run.py")
preds=rows(CLONE/"datasets"/"aeig-prediction-log.csv")
pros={r["prediction_id"]:r for r in preds if r.get("mode")=="prospective"}
dec=rows(CLONE/"datasets"/"aeig-l5-domain-decisions.csv") if (CLONE/"datasets"/"aeig-l5-domain-decisions.csv").exists() else []
man_status={}
for exp in ("EXP-CACHE-002","EXP-PLUGIN-001","EXP-RG-001","EXP-SCRIPT-001"):
    p=CLONE/"experiments"/"observatory"/"manifests"/f"{exp}.json"
    man_status[exp]=json.loads(p.read_text(encoding="utf-8-sig")).get("status")
final_rc=run(CLONE,"verify_aeig_static_rc.py")
post_release=run(CLONE,"audit_release_readiness.py")
version_path=CLONE/"VERSION"
progress_path=CLONE/"datasets"/"aeig-roadmap-progress.csv"
progress=rows(progress_path) if progress_path.exists() else []
met=sum(str(r.get("meets_1_0_target","")).lower() in {"true","1","yes"} for r in progress)
source_after={str(p):digest(p) for p in protected}
decmap={r.get("domain"):r for r in dec}
if REFUTE_PRED004:
    checks={
        "completion_orchestrator_blocks_refutation":pipeline.returncode!=0,
        "canonical_transaction_commit":"canonical transaction COMMIT" in pipeline.stdout,
        "pred004_refuted":pros.get("PRED-004",{}).get("status")=="refuted",
        "pred005_010_confirmed":all(pros.get(f"PRED-{i:03d}",{}).get("status")=="confirmed" for i in range(5,11)),
        "all_domain_evidence_captured":len(dec)==4 and all(str(r.get("evidence_ready","")).lower()=="true" for r in dec),
        "state_identity_revision_required":str(decmap.get("state-identity",{}).get("model_revision_required","")).lower()=="true",
        "other_domains_no_revision":all(str(decmap.get(d,{}).get("model_revision_required","")).lower()=="false" for d in ("cache","render-graph","plugin-host")),
        "manifests_observed":all(v=="observed" for v in man_status.values()),
        "version_not_created":not version_path.exists(),
        "coverage_remains_pre_release":len(progress)==27 and met==24,
        "static_rc_after_refutation":final_rc.returncode==0,
        "release_audit_remains_blocked":post_release.returncode!=0,
        "source_repository_unchanged":source_before==source_after,
        "canonical_aex_hash":aex_hash==EXPECTED_AEX,
        "suite_labels_48":len(labels)==48,
    }
else:
    checks={
        "completion_orchestrator_exit_zero":pipeline.returncode==0,
        "canonical_transaction_commit":"canonical transaction COMMIT" in pipeline.stdout,
        "completion_banner":"AEIG 1.0 COMPLETION ORCHESTRATOR: PASS" in pipeline.stdout,
        "predictions_004_010_confirmed":all(pros.get(f"PRED-{i:03d}",{}).get("status")=="confirmed" for i in range(4,11)),
        "decisions_ready":len(dec)==4 and all(str(r.get("evidence_ready","")).lower()=="true" and str(r.get("model_revision_required","")).lower()=="false" for r in dec),
        "manifests_observed":all(v=="observed" for v in man_status.values()),
        "version_1_0":version_path.exists() and version_path.read_text(encoding="utf-8-sig").strip()=="1.0",
        "coverage_27_27":len(progress)==27 and met==27,
        "static_rc_after_completion":final_rc.returncode==0,
        "release_audit_after_completion":post_release.returncode==0,
        "source_repository_unchanged":source_before==source_after,
        "canonical_aex_hash":aex_hash==EXPECTED_AEX,
        "suite_labels_48":len(labels)==48,
    }
passed=all(checks.values())
payload={"status":"PASS" if passed else "FAIL","date":date.today().isoformat(),
         "mode":MODE,"checks":checks,"orchestrator_exit":pipeline.returncode,"manifest_statuses":man_status,
         "prediction_statuses":{k:v.get("status") for k,v in pros.items()},
         "coverage_met":met}
OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
lines=["---","status: generated",f"last_verified: {date.today().isoformat()}","---",
       "# Finalizer Refutation-Path Self-Test" if REFUTE_PRED004 else "# Finalizer Success-Path Self-Test","",f"State: **{payload['status']}**.","",
       "| Check | Result |","|---|---|"]
for name,ok in checks.items(): lines.append(f"| `{name}` | **{'PASS' if ok else 'FAIL'}** |")
lines += ["","The test synthesizes a complete canonical-shaped operator capture inside a scratch clone, runs the real completion orchestrator used by FINISH (diagnose → finalizer → guarded promotion → final audits), and verifies prediction/domain/manifest commit plus 27/27 and VERSION=1.0 without touching live AE or canonical source state."]
PAGE.write_text("\n".join(lines)+"\n",encoding="utf-8")
for name,ok in checks.items(): print("PASS" if ok else "FAIL",name)
print("orchestrator_exit",pipeline.returncode,"coverage",met,"/",len(progress))
if not passed:
    print((pipeline.stdout+pipeline.stderr)[-5000:])
print("AEIG FINALIZER REFUTATION SELFTEST:" if REFUTE_PRED004 else "AEIG RAW-TO-RELEASE SELFTEST:",payload["status"])
shutil.rmtree(CLONE,ignore_errors=True)
raise SystemExit(0 if passed else 2)
