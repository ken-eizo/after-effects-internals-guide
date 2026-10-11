"""EXP-SHAPE-016: bounded callsite audit of operator vtable +0x18 (native evaluation).
Collect each concrete operator slot3 function and selected slot4/5; analyze call target
and argument setup, with version-pinned .pdata. Static, no host invocation.
"""
import pefile,subprocess,re,bisect,json,hashlib
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP,X86_OP_IMM
root=Path(r"D:\Developer\After Effects Internals Guide")
data=json.loads((root/"datasets/ae-vector-evaluator-vtable-slot-map-2025-2026.json").read_text())["versions"]
paths={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
"2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
out={}
for ver,path in paths.items():
 p=pefile.PE(path);base=p.OPTIONAL_HEADER.ImageBase;blob=Path(path).read_bytes()
 iat={imp.address:desc.dll.decode(errors="replace")+"!"+imp.name.decode(errors="replace") for desc in p.DIRECTORY_ENTRY_IMPORT for imp in desc.imports if imp.name}
 fs=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in p.DIRECTORY_ENTRY_EXCEPTION);starts=[e[0] for e in fs]
 md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
 rows=[]
 for row in data[ver]["rows"]:
  main=next((t for t in row["tables"] if t["subobject_offset"]==0),None)
  if not main:continue
  slots=[]
  for i in (3,4,5):
   slot=next((s for s in main["slots"] if s["index"]==i),None)
   if slot is None:continue
   rva=int(slot["func_rva"],16);ix=bisect.bisect_right(starts,rva)-1
   if ix<0 or rva>=fs[ix][1]:
    slots.append({"slot":i,"entry":hex(rva),"error":"no pdata function"});continue
   beg,end=fs[ix]
   limit=min(end-rva,6000)
   calls=[]
   ops=[]
   for ins in md.disasm(blob[p.get_offset_from_rva(rva):p.get_offset_from_rva(rva)+limit],base+rva):
    t=None
    if ins.mnemonic in ("call","jmp") and ins.operands:
     o=ins.operands[0]
     if o.type==X86_OP_IMM:t=o.imm
     if o.type==X86_OP_MEM and o.mem.base==X86_REG_RIP:t=ins.address+ins.size+o.mem.disp
    if t is not None:
     calls.append({"site":hex(ins.address-base),"target":hex(t-base),"module":iat.get(t,"")})
    if len(ops)<35:ops.append([hex(ins.address-base),ins.mnemonic,ins.op_str])
   slots.append({"slot":i,"entry":hex(rva),"pdata_begin":hex(beg),"pdata_end":hex(end),
                 "sample_bytes":limit,"calls":calls,"first_instructions":ops})
  rows.append({"matchName":row["matchName"],"class":row["concrete_rtti"],"slots":slots})
 out[ver]={"rows":rows,"sha256":hashlib.sha256(blob).hexdigest()}
 print("===",ver,"operators",len(rows),flush=True)
 for r in rows:
  v=next((x for x in r["slots"] if x["slot"]==3),None)
  print(r["matchName"],"EVAL",v["entry"] if v else "none","calls",len(v.get("calls",[])) if v else 0,flush=True)
  for c in (v or {}).get("calls",[])[:6]:print("  ",c["site"],c["module"][:95] or c["target"],flush=True)
dst=root/"datasets/ae-native-vector-evaluator-virtual-evaluation-2025-2026.json"
dst.write_text(json.dumps({"classification":"E2-L static evidence: vtable slot 3 callgraph and instruction prefixes","versions":out},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dst,flush=True)
