from pathlib import Path
import hashlib, json, py_compile, shutil, subprocess, sys, tempfile

ROOT = Path(r"D:\Developer\After Effects Internals Guide")
PKG = ROOT / "experiments" / "user-run" / "AEIG-1.0-L5"
AEX = PKG / "plugin" / "AEGP" / "AEIGReceiptArtie.aex"
EXPECTED = "DA8693DBD6B7CCC1BBF3043608D4FD7C93557D9CAF3F08A6B78D0BD5B6A1BB0F"
REQUIRED = [
    "00_PREPARE_RESULTS.cmd", "INSTALL_26_3.cmd", "01_RUN_IN_AE.jsx",
    "REMOVE_26_3.cmd", "02_VERIFY_RESULTS.cmd", "README.md",
    r"plugin\AEGP\AEIGReceiptArtie.aex",
]
ANALYZERS = [
    "analyze_receipt_experiment.py", "analyze_plugin_host_experiment.py",
    "analyze_rg_trace_experiment.py", "analyze_scripting_reflection.py",
    "verify_aeig_l5_user_run.py",
    "prepare_aeig_l5_user_run.py", "validate_observatory_manifests.py",
    "finalize_aeig_l5_user_run.py", "report_prediction_status.py",
    "selftest_aeig_analyzers.py", "complete_aeig_1_0_after_operator_run.py", "audit_pre_operator_readiness.py",
    "aeig_promotion_gate.py", "selftest_aeig_promotion_success.py", "selftest_aeig_promotion_transaction.py", "selftest_aeig_release_pipeline.py",
    "promote_aeig_1_0.py", "verify_aeig_static_rc.py",
    "aeig_prediction_semantics.py", "selftest_aeig_prediction_semantics.py",
    "selftest_aeig_prediction_lock_integrity.py",
    "aeig_file_transaction.py", "selftest_aeig_file_transaction.py",
    "selftest_aeig_finalizer_success.py",
    "aeig_operator_session.py", "selftest_aeig_operator_session.py",
]
errors = []
for rel in REQUIRED:
    if not (PKG / rel).exists(): errors.append(f"missing package file: {rel}")
sha = hashlib.sha256(AEX.read_bytes()).hexdigest().upper() if AEX.exists() else "MISSING"
if sha != EXPECTED: errors.append(f"AEX hash mismatch: {sha}")
TOOLS = ROOT / "probes" / "process-tools"
for name in ANALYZERS:
    p = TOOLS / name
    try: py_compile.compile(str(p), doraise=True)
    except Exception as e: errors.append(f"py_compile {name}: {e}")
for p in sorted((ROOT / "experiments" / "observatory" / "manifests").glob("*.json")):
    try: json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception as e: errors.append(f"manifest {p.name}: {e}")
jsx = PKG / "01_RUN_IN_AE.jsx"
readme=PKG/"README.md"
if readme.exists():
    rt=readme.read_text(encoding="utf-8-sig",errors="replace")
    for heading in ("## Operator session identity","## Fixture contract","## Evidence interpretation","## Trace safety","## Acceptance and release"):
        if heading not in rt: errors.append(f"README contract missing: {heading}")
if jsx.exists():
    jsx_text = jsx.read_text(encoding="utf-8-sig")
    tmp = PKG / "_syntax_check_tmp.js"
    tmp.write_text(jsx_text, encoding="utf-8")
    r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
    tmp.unlink(missing_ok=True)
    if r.returncode: errors.append("JSX syntax: " + (r.stderr or r.stdout).strip())
    fixture_sequence = [
        'comp.renderer="AEIG Receipt Probe"', '"AEIG_SOLID",32,32,1,1', 'layer.threeDLayer=true',
        'e1.property(1).setValue(10)', 'e1.property(1).setValue(9)', 'renderPass(comp,"WARMUP"',
        'e1.property(1).setValue(10); log("POST_WARMUP blur="', 'CANONICAL_CAPTURE_RESET_AFTER_WARMUP',
        'renderPass(comp,"A"',
        'e1.property(1).setValue(75)', 'log("MUTATION blur="+e1.property(1).value)', 'renderPass(comp,"B"',
    ]
    pos = [jsx_text.find(x) for x in fixture_sequence]
    if any(x < 0 for x in pos): errors.append("JSX fixture guard: required 3D/rebind sequence missing")
    elif pos != sorted(pos): errors.append("JSX fixture guard: render/mutation sequence out of order")
    if jsx_text.count('layer=comp.layer("AEIG_SOLID")') < 3 or jsx_text.count('e1=fx.property(1)') < 3:
        errors.append("JSX fixture guard: effect references must be rebound before WARMUP, after WARMUP, and after pass A")
    for token in ('var SESSION = ','readKV(SESSION)','aeig.session_id=','aeig.static_rc_fingerprint=','SESSION_ID='):
        if token not in jsx_text: errors.append("JSX operator-session contract missing: "+token)
prep_tool=TOOLS/"prepare_aeig_l5_user_run.py"
if prep_tool.exists():
    pt=prep_tool.read_text(encoding="utf-8-sig",errors="replace")
    for token in ("aeig-l5-operator-session.env","static_rc_fingerprint","operator_session"):
        if token not in pt: errors.append("prepare session contract missing: "+token)

# Outer wrappers are part of the release handoff contract.
PREP=ROOT / "experiments" / "user-run" / "AEIG-L5-PREPARE.cmd"
STATUS=ROOT / "experiments" / "user-run" / "AEIG-L5-STATUS.cmd"
FINISH=ROOT / "experiments" / "user-run" / "AEIG-L5-FINISH.cmd"
for wrapper in (PREP, STATUS, FINISH):
    if not wrapper.exists(): errors.append(f"missing wrapper: {wrapper.relative_to(ROOT)}")
if PREP.exists():
    t=PREP.read_text(encoding="utf-8-sig",errors="replace")
    p0=t.find("preflight_aeig_l5_operator_run.py")
    allow=t.find("--allow-stale-capture",p0) if p0>=0 else -1
    archive=t.find("00_PREPARE_RESULTS.cmd")
    p1=t.find("preflight_aeig_l5_operator_run.py",p0+1) if p0>=0 else -1
    install=t.find("INSTALL_26_3.cmd")
    if min(p0,allow,archive,p1,install)<0 or not (p0<=allow<archive<p1<install):
        errors.append("PREP wrapper order/safety contract invalid")
    if "AEIG_NO_PAUSE=1" not in t: errors.append("PREP wrapper missing noninteractive child mode")
if STATUS.exists():
    t=STATUS.read_text(encoding="utf-8-sig",errors="replace")
    if "status_aeig_l5_operator_run.py" not in t: errors.append("STATUS wrapper contract invalid")
if FINISH.exists():
    t=FINISH.read_text(encoding="utf-8-sig",errors="replace")
    ordered=["REMOVE_26_3.cmd","complete_aeig_1_0_after_operator_run.py"]
    pos=[t.find(x) for x in ordered]
    if any(x<0 for x in pos) or pos!=sorted(pos): errors.append("FINISH wrapper order contract invalid")
    if "AEIG_NO_PAUSE=1" not in t: errors.append("FINISH wrapper missing noninteractive child mode")
for name in ("00_PREPARE_RESULTS.cmd","INSTALL_26_3.cmd","REMOVE_26_3.cmd","02_VERIFY_RESULTS.cmd"):
    cp=PKG/name
    if cp.exists() and "AEIG_NO_PAUSE" not in cp.read_text(encoding="utf-8-sig",errors="replace"):
        errors.append(f"{name}: missing AEIG_NO_PAUSE support")
install=PKG/"INSTALL_26_3.cmd"
if install.exists():
    t=install.read_text(encoding="utf-8-sig",errors="replace")
    ordered=["preflight_aeig_l5_operator_run.py","copy /Y","fc /B"]
    pos=[t.find(x) for x in ordered]
    if any(x<0 for x in pos) or pos!=sorted(pos):
        errors.append("INSTALL contract: preflight/copy/byte-verify order invalid")
finalizer=TOOLS/"finalize_aeig_l5_user_run.py"
if finalizer.exists() and "verify_aeig_static_rc.py" not in finalizer.read_text(encoding="utf-8-sig",errors="replace"):
    errors.append("finalizer contract: missing Static RC fail-closed gate")
verify_cmd=PKG/"02_VERIFY_RESULTS.cmd"
if verify_cmd.exists() and "finalize_aeig_l5_user_run.py" not in verify_cmd.read_text(encoding="utf-8-sig",errors="replace"):
    errors.append("02_VERIFY_RESULTS contract: finalizer is not invoked")

old_hashes = ["8FAD5221BC5AA270CFF9505F6E3F2ABF7916F4B4DFE7820BA653DFDA759E9FEE",
              "9D74BE748771D60A63CF3770E346DC7D69348BB5C8B007235CB325FBAF5D9AAB",
              "9768BC9B463F6377E1AE246303D6AEDD8BF11725E8D96034DF14E85F1AD9BE98",
              "E3546DB78AA3454FEE5EF6C5A14A3B1152111D2A543E249C3DBB1036AE3DFF33",
              "01B019CFE9AF26A7CB5B8580F9C5297D263FB8742BFBF06721A79BD6E7725062",
              "884E9CB19AF32AFA1DBFB11A4777E66107C71B13C16A759FBB9B299572382792"]
text_ext = {".md", ".json", ".py", ".cmd", ".jsx", ".txt", ".csv", ".tsv", ".h", ".cpp"}
for base in [PKG, ROOT / "experiments" / "observatory" / "manifests", TOOLS]:
    for p in base.rglob("*"):
        if p.resolve() == Path(__file__).resolve(): continue
        if not p.is_file() or p.suffix.lower() not in text_ext: continue
        try: text = p.read_text(encoding="utf-8-sig", errors="replace")
        except Exception: continue
        for old in old_hashes:
            if old in text: errors.append(f"stale hash {old[:12]} in {p.relative_to(ROOT)}")
print(f"package_files={sum((PKG / r).exists() for r in REQUIRED)}/{len(REQUIRED)}")
print(f"aex_sha256={sha}")
print(f"python_compile={len(ANALYZERS)}/{len(ANALYZERS)}")
print("manifest_json=ok" if not any(e.startswith("manifest ") for e in errors) else "manifest_json=fail")
print("jsx_syntax=ok" if not any(e.startswith("JSX syntax") for e in errors) else "jsx_syntax=fail")
if errors:
    print("errors:")
    for e in errors: print(" -", e)
    sys.exit(1)
print("AEIG-L5 package audit: GREEN")

