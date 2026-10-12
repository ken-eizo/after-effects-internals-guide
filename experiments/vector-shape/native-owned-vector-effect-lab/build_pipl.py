"""Build the AEGP PiPL .rc using the locally installed Adobe SDK's PiPLTool.
Never copy or distribute SDK headers or PiPLTool with this repository.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile

p = argparse.ArgumentParser()
p.add_argument("--cl", required=True)
p.add_argument("--sdk", required=True)
p.add_argument("--source", required=True)
p.add_argument("--output", required=True)
a = p.parse_args()
sdk = Path(a.sdk)
tool = sdk / "Resources" / "PiPLtool.exe"
if not tool.exists():
    raise SystemExit(f"Adobe PiPLtool.exe missing: {tool}")
dest = Path(a.output)
dest.parent.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory() as t:
    rr = Path(t) / "ShapeLayerProbe_PiPL.rr"
    rrc = Path(t) / "ShapeLayerProbe_PiPL.rrc"
    command1 = [a.cl, "/nologo", "/EP", f"/I{sdk / 'Headers'}", a.source]
    first = subprocess.run(command1, check=True, capture_output=True)
    rr.write_bytes(first.stdout)
    subprocess.run([str(tool), str(rr), str(rrc)], check=True, capture_output=True)
    command2 = [a.cl, "/nologo", "/DMSWindows", "/EP", str(rrc)]
    second = subprocess.run(command2, check=True, capture_output=True)
    dest.write_bytes(second.stdout)
print(f"Generated PiPL resource: {dest}")
