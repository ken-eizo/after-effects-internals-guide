"""Verify ShapeLayerAE and AEIG research artifacts without mutating existing AEIG records."""
from pathlib import Path
import json
import subprocess
import sys
import hashlib

aeig = Path(r"D:\Developer\After Effects Internals Guide")
root = Path(__file__).resolve().parents[1]
for path in sorted((aeig / "experiments/observatory/manifests").glob("EXP-SHAPE-*.json")):
    x = json.loads(path.read_text(encoding="utf-8"))
    print("VALID_JSON:", path.name, "status:", x.get("status"))
aex = root / "build/Release/ShapeLayerAE.aex"
print("BUILT_AEX_EXISTS:", aex.is_file())
if aex.is_file():
    print("BUILT_AEX_SHA256:", hashlib.sha256(aex.read_bytes()).hexdigest())
expected_page = aeig / "docs/vector-shape-system/native-extensibility-boundaries.md"
print("AEIG_RESEARCH_PAGE_EXISTS:", expected_page.is_file())
py = aeig / "scratch/.venv-docs/Scripts/python.exe"
if not py.is_file():
    print("MKDOCS_CHECK_SKIPPED: missing AEIG .venv-docs")
    raise SystemExit(0)
out = root / "build/aeig-site-qa"
command = [str(py), "-m", "mkdocs", "build", "--strict", "-d", str(out)]
cp = subprocess.run(command, cwd=str(aeig), capture_output=True, text=True, errors="replace")
log = root / "build/aeig_mkdocs_qa.log"
log.write_text(cp.stdout + "\n" + cp.stderr, encoding="utf-8")
print("MKDOCS_STRICT_EXIT:", cp.returncode)
print("MKDOCS_PAGE_GENERATED:", (out / "vector-shape-system/native-extensibility-boundaries/index.html").is_file())
print("MKDOCS_LOG:", log)
print("LAST_LOG_LINES:")
print("\n".join((cp.stdout + "\n" + cp.stderr).splitlines()[-12:]))
raise SystemExit(cp.returncode)
