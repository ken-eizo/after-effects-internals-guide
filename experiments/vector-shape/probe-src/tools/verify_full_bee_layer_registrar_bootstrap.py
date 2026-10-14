"""Verify nine built-in BEE Layer-family stream registrars share one birth/death helper.
Read-only, exact installed AE2025/2026 BEE SHA-gated; no host calls.
"""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[4]
DATA=ROOT/"datasets"/"ae-bee-full-layer-family-registration-bootstrap-2025-2026.json"
report=json.loads(DATA.read_text(encoding="utf-8"))
FAMILIES=("BEE_Layer","BEE_AVLayer","BEE_MaterialOverrideLayer","BEE_TextLayer",
          "BEE_VectorLayer","BEE_CameraLayer","BEE_LightLayer","BEE_ModelLayer",
          "BEE_ParametricMeshLayer")
CONFIG={
"2025":{"dll":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
"sha":"98c682351e30f38cb7021eaa142f5ec473aea92885e14915d87c157cda971730",
"birth":"0x64a530","death":"0x64b090","reg":"0x36dd90","unreg":"0x36def0"},
"2026":{"dll":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"),
"sha":"5fd8d318456228b9fd2a6733a5758f6b84206b7a8effcba5202957cd27ac680e",
"birth":"0x664f70","death":"0x6659a0","reg":"0x3787b0","unreg":"0x378910"}}
def source_match(records,caller):
 found=[x for x in records if x["caller_function_rva"]==caller and x["branch"]=="call"]
 assert len(found)==1,(caller,found)
 return found[0]["site"]
for year,c in CONFIG.items():
 r=report["versions"][year];t=r["targets"]
 assert r["sha256"]==c["sha"]==hashlib.sha256(c["dll"].read_bytes()).hexdigest()
 def target(exact):
  hits=[(name,val) for name,val in t.items() if name==exact]
  assert len(hits)==1,(year,exact,len(hits))
  return hits[0][1]
 ini=target("LOCAL_RegisterStreams_bootstrap_0")
 end=target("LOCAL_RegisterStreams_bootstrap_1")
 assert ini["rva"]==c["reg"] and end["rva"]==c["unreg"]
 source_match(ini["verified_direct_calls"],c["birth"])
 source_match(end["verified_direct_calls"],c["death"])
 for name in FAMILIES:
  register=target(f"?RegisterStreams@{name}@@"+("SAX_N@Z" if name=="BEE_Layer" else "SAXPEBE@Z" if name=="BEE_AVLayer" else "SAXXZ"))
  source_match(register["verified_direct_calls"],c["reg"])
  if name=="BEE_Layer":
   source_match(register["verified_direct_calls"],c["unreg"])
  else:
   unregister=target(f"?UnregisterStreams@{name}@@SAXXZ")
   source_match(unregister["verified_direct_calls"],c["unreg"])
 print("PASS",year,"9 built-in stream registration families, 9 teardown call edges, birth/death linking, DLL SHA256")
print("PASS 2/2 versions; direct-call census scoped to BEE; no external Layer provider discovered by this test.")
