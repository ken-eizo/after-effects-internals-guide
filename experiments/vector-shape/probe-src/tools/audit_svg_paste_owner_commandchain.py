"""EXP-SHAPE-020 native SVG paste ownership and generic Layer IndexedStream gate.
Static exact-binary PE analysis only. No Adobe callbacks executed. No runtime modification.
Exports selected by NAME; full function bounds determined by x64 .pdata.
"""
from pathlib import Path
import pefile,subprocess,re,json,hashlib,bisect
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_OP_IMM,X86_REG_RIP
r=Path(r"D:\Developer\After Effects Internals Guide")
binaries={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
          "2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")}
targets=["BEE_CmdPasteSVGIntoLayer@@","BEE_PasteSVGIntoComp@@",
         "BEE_CmdAddToIndexedStreamGroup@@","BEE_CmdAddVectorProperty@@",
         "BEE_IsShapeGroupOwnerStreamPath@@","BEE_IsShapeGroupStreamPath@@",
         "BEE_IsShapeStreamPath@@","BEE_GetShapePathsVec@@",
         "BEE_CmdNewVectorLayer@@","BEE_CmdNewVectorLayer@@",
         "BEE_Layer::ScSuppressStreamReordered"]
rx=re.compile(r"^\s*\d+\s+[0-9a-fA-F]+\s+([0-9a-fA-F]{8})\s+(\S+)")
res={}
for ver,path in binaries.items():
 print("BEGIN",ver,flush=True)
 raw=path.read_bytes();p=pefile.PE(data=raw);base=p.OPTIONAL_HEADER.ImageBase
 exports={}
 for line in subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,errors="replace",check=True).stdout.splitlines():
  m=rx.match(line)
  if m:exports[int(m.group(1),16)]=m.group(2)
 imports={imp.address:desc.dll.decode(errors="replace")+"!"+imp.name.decode(errors="replace") for desc in p.DIRECTORY_ENTRY_IMPORT for imp in desc.imports if imp.name}
 spans=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION)
 begins=[x[0] for x in spans]
 cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
 rows=[]
 for target in targets:
  matches=[(rva,name) for rva,name in exports.items() if target in name]
  if len(matches)==0:
   rows.append({"query":target,"present":False});continue
  for rv,name in matches:
   k=bisect.bisect_right(begins,rv)-1
   if k<0 or rv>=spans[k][1]:
    rows.append({"query":target,"symbol":name,"function_start":hex(rv),"error":"no x64 pdata"});
    continue
   beg,end=spans[k]
   calls=[];inst_prefix=[]
   for ins in cs.disasm(raw[p.get_offset_from_rva(beg):p.get_offset_from_rva(beg)+(end-beg)],base+beg):
    if len(inst_prefix)<95:inst_prefix.append([hex(ins.address-base),ins.mnemonic,ins.op_str])
    if ins.mnemonic not in ("call","jmp") or not ins.operands:continue
    op=ins.operands[0];addr=None
    if op.type==X86_OP_IMM:addr=op.imm
    elif op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:addr=ins.address+ins.size+op.mem.disp
    tar=addr-base if addr is not None else None
    sym=(exports.get(tar) or imports.get(addr)) if addr is not None else ""
    calls.append({"site":hex(ins.address-base),"destination_rva":hex(tar) if tar is not None else None,"callee":sym or "","insn":ins.mnemonic+" "+ins.op_str})
   focused=[c for c in calls if any(z.lower() in c["callee"].lower() for z in
      ("vector","shape","stream","layer","svg","art","group","TDB","BEE_Cmd","AGM","source","ScSuppress"))]
   rows.append({"query":target,"symbol":name,"function_start":hex(beg),"function_end":hex(end),
                "instructions_prefix":inst_prefix,"direct_and_indirect_calls":calls,
                "focused_calls":focused})
   print("\nFUNCTION",name[:155],"RVA",hex(beg),"SIZE",end-beg,
         "TOTAL CALLS",len(calls),"FOCUSED",len(focused),flush=True)
   for c in focused[:95]:print(" ",c["site"],c["callee"][:185],flush=True)
 res[ver]={"source_sha256":hashlib.sha256(raw).hexdigest(),"functions":rows}
dest=r/"datasets/ae-native-svg-paste-stream-owner-commandchain-2025-2026.json"
dest.write_text(json.dumps({"classification":"E2-L .pdata bounded static call graph; indirect interface methods may be unresolved","versions":res},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dest,flush=True)
