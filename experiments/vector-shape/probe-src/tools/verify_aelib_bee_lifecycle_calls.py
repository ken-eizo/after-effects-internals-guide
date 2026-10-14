"""Validate aelib -> BEE_Birth/Death exact imports and native callsites.
Pinned PE hash gating; no host execution.
"""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[4]
DATA=ROOT/"datasets"/"ae-aelib-bee-lifecycle-crossmodule-2025-2026.json"
d=json.loads(DATA.read_text(encoding="utf-8"))
cfg={
"2025":{"path":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\aelib.dll"),
"birth":{"0x6e272":"0x6d9b0","0x6f6cf":"0x6f550"},"death":{"0x6ef56":"0x6edc0"}},
"2026":{"path":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\aelib.dll"),
"birth":{"0x70647":"0x6fd80","0x71bc8":"0x71a60"},"death":{"0x712e6":"0x71150"}}
}
for year,c in cfg.items():
 record=d["versions"][year]
 assert record["aelib_sha256"]==hashlib.sha256(c["path"].read_bytes()).hexdigest(),year
 entries=record["imports"]
 birth=[v for k,v in entries.items() if "?BEE_Birth@@" in k]
 death=[v for k,v in entries.items() if "?BEE_Death@@" in k]
 assert len(birth)==1 and len(death)==1,year
 for name,rows,expected in (("Birth",birth[0]["verified_code_references"],c["birth"]),("Death",death[0]["verified_code_references"],c["death"])):
  assert {v["site"]:v["caller_function_rva"] for v in rows}==expected,(year,name,rows)
  assert all(v["kind"]=="call" for v in rows)
  print("PASS",year,name,len(rows),"instruction-boundary verified imports")
print("PASS 2/2 cross-module startup/teardown import boundary; native extension class registration still unproven")
