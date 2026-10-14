"""Validate exact pinned AE2025/2026 native attachment-contract evidence.
Read-only. Reads extracted disassembly plus original DLL fingerprints.
"""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parent
DATA=ROOT.parents[3]/"datasets"/"ae-bee-compitem-attach-owner-contract-2025-2026.json"
CFG={
 "2025":{"dll":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),"entry":"0x392120","layer":"mov ebp, dword ptr [rbx + 0x2d8]","vcall":"call qword ptr [rax + 0x550]","counter":"inc dword ptr [rsi + 0x3c8]"},
 "2026":{"dll":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"),"entry":"0x39d4d0","layer":"mov ebp, dword ptr [rbx + 0x26c]","vcall":"call qword ptr [rax + 0x560]","counter":"inc dword ptr [rsi + 0x420]"}
}
d=json.loads(DATA.read_text(encoding="utf-8"))
for y,expected in CFG.items():
 item=d["versions"][y]
 rows=item["functions"]["attach"]["instructions"]
 actual={r["asm"]:[int(v["rva"],16) for v in rows if v["asm"]==r["asm"]] for r in rows}
 assert item["functions"]["attach"]["entry"]==expected["entry"],y
 assert hashlib.sha256(expected["dll"].read_bytes()).hexdigest()==item["SHA256"],y
 for k in ("layer","vcall","counter"):
  assert len(actual.get(expected[k],[]))==1,(y,k,actual.get(expected[k]))
 for v in (1,2,5,7):
  assert any(row["asm"]=="mov edx, "+str(v) for row in rows),(y,v)
 assert len(actual.get("call qword ptr [rax + 0x278]",[]))==4,y
 assert min(actual[expected["layer"]])<min(actual[expected["vcall"]]),y
 assert min(actual[expected["layer"]])<min(actual[expected["counter"]]),y
 assert item["functions"]["partial_attach"]["instructions"],y
 print("PASS",y,"SHA256",item["SHA256"],"attach",expected["entry"],
       "object-field",expected["layer"],"virtual",expected["vcall"],
       "conditional counter",expected["counter"])
print("PASS 2/2 pinned native binaries; bounded static host-attach contract verified; external admission NOT proven")
