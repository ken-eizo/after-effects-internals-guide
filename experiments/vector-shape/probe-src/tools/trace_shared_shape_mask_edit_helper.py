"""Analyze shared native BEE shape/mask RESET helper by .pdata and direct call
sites. Offline binary inspection only; no After Effects commands run.
"""
import pefile,hashlib,json,bisect
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
data={}
for year,path,helper in (
("2025",r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x67a350),
("2026",r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x696380)):
 raw=Path(path).read_bytes();p=pefile.PE(data=raw);base=p.OPTIONAL_HEADER.ImageBase
 names={s.address:s.name.decode(errors="replace") for s in p.DIRECTORY_ENTRY_EXPORT.symbols if s.name}
 reg=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION)
 ix=bisect.bisect_right([x[0] for x in reg],helper)-1
 assert ix>=0 and helper<reg[ix][1]
 start,end=reg[ix];assert end-start<40000,(year,hex(end-start))
 md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
 ins=[];calls=[]
 for x in md.disasm(raw[p.get_offset_from_rva(start):p.get_offset_from_rva(end)],base+start):
  if len(ins)<80:ins.append({"rva":hex(x.address-base),"op":x.mnemonic,"args":x.op_str})
  dest=None
  if x.mnemonic in ("call","jmp") and x.operands:
   op=x.operands[0]
   if op.type==X86_OP_IMM:dest=op.imm-base
   elif op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
    dest=x.address+x.size+op.mem.disp-base
  if dest is not None:
   calls.append({"site":hex(x.address-base),"target":hex(dest),"symbol":names.get(dest,"")})
 data[year]={"sha256":hashlib.sha256(raw).hexdigest(),"entry":hex(helper),
             "pdata":[hex(start),hex(end)],"first":ins,"direct_calls":calls}
 print("YEAR",year,"helper",hex(helper),"pdata",hex(start),hex(end),"calls",len(calls),flush=True)
 for c in calls[:65]:print(c["site"],c["symbol"][:120] or c["target"],flush=True)
dst=Path(r"D:\Developer\ShapeLayerAE\results\shared_shape_mask_edit_helper_2025_2026.json")
dst.write_text(json.dumps({"evidence":"E2-L read-only native disassembly","versions":data},indent=2)+"\n",encoding="utf8")
print("SAVED",dst)
