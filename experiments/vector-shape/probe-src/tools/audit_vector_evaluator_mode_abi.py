"""Classify native vector operator evaluate(mode, context) ABI dispatch for 20 types.
Determine whether mode gate accepts 0 or 1 and identify indirect virtual delegate offset.
Static read-only PE; branch controls are evidence, C++ prototype is not reconstructed.
"""
from pathlib import Path
import json,pefile,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
root=Path(r"D:\Developer\After Effects Internals Guide")
vt=json.loads((root/"datasets/ae-vector-evaluator-vtable-slot-map-2025-2026.json").read_text())["versions"]
binaries={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
          "2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
data={}
for ver,path in binaries.items():
 pe=pefile.PE(path);blob=Path(path).read_bytes();base=pe.OPTIONAL_HEADER.ImageBase
 decoder=Cs(CS_ARCH_X86,CS_MODE_64)
 entries=[]
 for row in vt[ver]["rows"]:
  primary=next(t for t in row["tables"] if t["subobject_offset"]==0)
  entry=next(x for x in primary["slots"] if x["index"]==3)
  start=int(entry["func_rva"],16)
  dis=list(decoder.disasm(blob[pe.get_offset_from_rva(start):pe.get_offset_from_rva(start)+0x84],base+start))
  # Only inspect initial mode selector before subsequent independent functions in .text
  initial=dis[:min(len(dis),28)]
  mode0=any(i.mnemonic=="test" and i.op_str=="edx, edx" for i in initial)
  mode1=any(i.mnemonic=="cmp" and i.op_str=="edx, 1" for i in initial)
  kind="native-filter-mode-1" if mode1 and not mode0 else ("native-shape-graphic-mode-0" if mode0 and not mode1 else "unclassified")
  dlist=[{"rva":hex(i.address-base),"op":i.mnemonic,"operands":i.op_str} for i in initial]
  entries.append({"MatchName":row["matchName"],"entry_rva":hex(start),"kind":kind,"initial":dlist})
 c0=sum(r["kind"]=="native-shape-graphic-mode-0" for r in entries)
 c1=sum(r["kind"]=="native-filter-mode-1" for r in entries)
 assert (c0,c1)==(9,11),(ver,c0,c1)
 data[ver]={"sha256":hashlib.sha256(blob).hexdigest(),"mode0_count":c0,"mode1_count":c1,"entries":entries}
 print(ver,"MODE0",c0,"MODE1",c1,flush=True)
dest=root/"datasets/ae-vector-evaluator-mode-abi-2025-2026.json"
dest.write_text(json.dumps({"classification":"E2-L static mode gate at vtable +0x18, no private API or callback invocation","versions":data},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dest,flush=True)
