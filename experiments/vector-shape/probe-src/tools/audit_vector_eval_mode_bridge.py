"""Expose +0x18 vtable bridge code for representative AE Vector Operators.
Disassembles bounded fixed 0x120-byte windows to include cold ranges outside pdata.
Static PE only. Do not execute private functions.
"""
from pathlib import Path
import pefile,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
r=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-vector-evaluator-vtable-slot-map-2025-2026.json")
data=json.loads(r.read_text())["versions"]
items={"ADBE Vector Filter - Trim","ADBE Vector Filter - Repeater","ADBE Vector Group",
       "ADBE Vector Shape - Group","ADBE Vector Shape - Rect","ADBE Vector Graphic - Fill"}
for ver,path in [("2025",r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
                 ("2026",r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")]:
 p=pefile.PE(path);b=Path(path).read_bytes();base=p.OPTIONAL_HEADER.ImageBase
 print("\n==========================",ver,flush=True)
 for row in data[ver]["rows"]:
  if row["matchName"] not in items:continue
  table=next(t for t in row["tables"] if t["subobject_offset"]==0)
  slot=next(s for s in table["slots"] if s["index"]==3)
  start=int(slot["func_rva"],16)
  print("\n=== "+row["matchName"]+" slot3 "+hex(start),flush=True)
  for ins in Cs(CS_ARCH_X86,CS_MODE_64).disasm(b[p.get_offset_from_rva(start):p.get_offset_from_rva(start)+0x128],base+start):
   print("%08x %-10s %s"%(ins.address-base,ins.mnemonic,ins.op_str),flush=True)
