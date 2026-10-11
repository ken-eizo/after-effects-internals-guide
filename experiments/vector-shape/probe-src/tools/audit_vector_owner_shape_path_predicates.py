"""EXP-SHAPE-021 parse exact x64 path predicates & owner command, RIP data references.
Proves when stream-path classification depends on tail MatchNames rather than owner type;
does NOT prove any foreign owner is accepted by editor/render.
"""
from pathlib import Path
import pefile,subprocess,re,json,hashlib,bisect
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP,X86_OP_IMM
root=Path(r"D:\Developer\After Effects Internals Guide")
paths={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
       "2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")}
queries=["BEE_IsShapeGroupOwnerStreamPath@@","BEE_IsShapeGroupStreamPath@@",
         "BEE_IsShapeStreamPath@@","BEE_GetShapePathsVec@@","BEE_CmdAddToIndexedStreamGroup@@"]
rx=re.compile(r"^\s*\d+\s+[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s+(\S+)")
out={}
for ver,pth in paths.items():
 raw=pth.read_bytes();pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase
 symbols={}
 for line in subprocess.run(["dumpbin","/exports",str(pth)],capture_output=True,text=True,errors="replace",check=True).stdout.splitlines():
  m=rx.match(line)
  if m:symbols[int(m.group(1),16)]=m.group(2)
 spans=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in pe.DIRECTORY_ENTRY_EXCEPTION);starts=[x[0] for x in spans]
 decoder=Cs(CS_ARCH_X86,CS_MODE_64);decoder.detail=True
 records=[]
 for q in queries:
  entries=[(r,n) for r,n in symbols.items() if q in n]
  for start,name in entries:
   idx=bisect.bisect_right(starts,start)-1
   beg,end=spans[idx]
   assert beg<=start<end
   inst=[]
   for op in decoder.disasm(raw[pe.get_offset_from_rva(beg):pe.get_offset_from_rva(beg)+(end-beg)],base+beg):
    refs=[]
    for operand in op.operands:
     if operand.type==X86_OP_MEM and operand.mem.base==X86_REG_RIP:
      ref=op.address+op.size+operand.mem.disp-base
      refs.append({"rva":hex(ref),"export":symbols.get(ref,""),"section":next((s.Name.decode(errors="replace").rstrip(chr(0)) for s in pe.sections if s.VirtualAddress<=ref<s.VirtualAddress+s.Misc_VirtualSize),"")})
    inst.append({"rva":hex(op.address-base),"opcode":op.mnemonic,"operands":op.op_str,"rip_refs":refs})
   r={"query":q,"symbol":name,"start":hex(beg),"end":hex(end),"instructions":inst}
   records.append(r)
   print("====",ver,q,hex(beg),"instructions",len(inst),flush=True)
   if "BEE_IsShape" in q:
    for ins in inst:print(ins["rva"],ins["opcode"],ins["operands"],
     "DATA "+",".join(x["rva"]+" "+x["export"][:70] for x in ins["rip_refs"]),flush=True)
   elif q=="BEE_GetShapePathsVec@@":
    for ins in inst:print(ins["rva"],ins["opcode"],ins["operands"],
     "DATA "+",".join(x["rva"]+" "+x["export"][:60] for x in ins["rip_refs"]),flush=True)
   else:
    for ins in inst[:45]:print(ins["rva"],ins["opcode"],ins["operands"],flush=True)
 out[ver]={"sha256":hashlib.sha256(raw).hexdigest(),"functions":records}
dest=root/"datasets/ae-vector-owner-shape-path-predicate-disassembly-2025-2026.json"
dest.write_text(json.dumps({"classification":"E2-L static x64 code, no AE host private API executed","versions":out},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dest,flush=True)
