"""Fail-closed verification of direct native BEE_Birth/BEE_Death stream-registration edges.
Only compares pinned local DLL hashes and static direct-call evidence.
"""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[4]
DATA=ROOT/"datasets"/"ae-bee-native-layer-stream-birth-death-2025-2026.json"
d=json.loads(DATA.read_text(encoding="utf-8"))
CFG={
 "2025":{"path":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
 "birth":"0x64a530","death":"0x64b090","bootstrap_init":"0x36dd90","bootstrap_shutdown":"0x36def0"},
 "2026":{"path":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",
 "birth":"0x664f70","death":"0x6659a0","bootstrap_init":"0x3787b0","bootstrap_shutdown":"0x378910"}
}
def one(rows,caller):
 matches=[x for x in rows if x["caller_function_rva"]==caller and x["branch"]=="call"]
 assert len(matches)==1,(caller,rows)
 return matches[0]["site"]
for year,cfg in CFG.items():
 record=d["versions"][year]
 assert hashlib.sha256(Path(cfg["path"]).read_bytes()).hexdigest()==record["sha256"],year
 targets=record["targets"]
 def get(needle):
  hits=[v for name,v in targets.items() if needle in name]
  assert len(hits)==1,(year,needle,[k for k in targets if needle in k])
  return hits[0]
 init=get("LOCAL_RegisterStreams_bootstrap_0")
 shutdown=get("LOCAL_RegisterStreams_bootstrap_1")
 assert init["rva"]==cfg["bootstrap_init"] and shutdown["rva"]==cfg["bootstrap_shutdown"]
 assert one(init["verified_direct_calls"],cfg["birth"])
 assert one(shutdown["verified_direct_calls"],cfg["death"])
 for family in ("BEE_Layer","BEE_AVLayer","BEE_TextLayer","BEE_VectorLayer"):
  reg=get("?RegisterStreams@"+family+"@@")
  assert one(reg["verified_direct_calls"],cfg["bootstrap_init"])
  if family=="BEE_Layer":
   assert one(reg["verified_direct_calls"],cfg["bootstrap_shutdown"])
  else:
   unreg=get("?UnregisterStreams@"+family+"@@")
   assert one(unreg["verified_direct_calls"],cfg["bootstrap_shutdown"])
 print("PASS",year,"Birth -> common registrar -> four registered families; Death -> unregistration for all four; DLL SHA256 matched")
print("PASS 2/2. Only verified direct-call edges; independent extension API remains unproven.")
