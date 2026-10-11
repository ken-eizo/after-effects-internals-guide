"""Static BEE generic and vector-specific stream edit-path boundary.
No private host code executed. Pinned AE2025/2026 BEE PE analysis.
"""
import pefile,hashlib,json,bisect
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
names=("?BEE_SetStreamFPV@@","?BEE_CmdSetStreamFPV@@","?BEE_CmdSetStreamFPVPlus@@",
"?BEE_CmdResetVectorShape@@","?BEE_CmdResetMaskShape@@",
"?BEE_CmdAddToIndexedStreamGroup@@","?BEE_CmdAddVectorProperty@@")
files={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
"2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
report={}
for year,path in files.items():
 raw=Path(path).read_bytes();p=pefile.PE(data=raw);base=p.OPTIONAL_HEADER.ImageBase
 ex={i.address:i.name.decode(errors="replace") for i in p.DIRECTORY_ENTRY_EXPORT.symbols if i.name}
 pd=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION)
 beg=[t[0] for t in pd]
 dis=Cs(CS_ARCH_X86,CS_MODE_64);dis.detail=True
 entries=[]
 for name in names:
  matches=[(r,s) for r,s in ex.items() if s.startswith(name)]
  assert len(matches)==1,(year,name,matches)
  r,s=matches[0];i=bisect.bisect_right(beg,r)-1
  assert i>=0 and r<pd[i][1],(year,name)
  stop=min(pd[i][1],r+15000)
  buf=raw[p.get_offset_from_rva(r):p.get_offset_from_rva(stop)]
  calls=[];first=[]
  for x in dis.disasm(buf,base+r):
   target=None
   if x.mnemonic in ("call","jmp") and x.operands:
    op=x.operands[0]
    if op.type==X86_OP_IMM:target=op.imm-base
    elif op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
     target=x.address+x.size+op.mem.disp-base
   if target is not None:
    calls.append({"site":hex(x.address-base),"destination_rva":hex(target),
                  "symbol":ex.get(target,"")})
   if len(first)<25:first.append(x.mnemonic+" "+x.op_str)
  entries.append({"name":s,"rva":hex(r),"pdata_end":hex(pd[i][1]),"calls":calls,
                  "first_instructions":first})
  print(year,name,"direct",len(calls),flush=True)
  for t in calls[:10]:print(" ",t["site"],t["symbol"][:100] or t["destination_rva"],flush=True)
 report[year]={"sha256":hashlib.sha256(raw).hexdigest(),"functions":entries}
dst=Path(r"D:\Developer\ShapeLayerAE\results\native_vector_generic_stream_write_contract_2025_2026.json")
dst.write_text(json.dumps({"evidence":"E2-L pinned BEE static direct calls only; unknown native plugin owner","versions":report},indent=2)+"\n",encoding="utf8")
print("SAVED",dst)
