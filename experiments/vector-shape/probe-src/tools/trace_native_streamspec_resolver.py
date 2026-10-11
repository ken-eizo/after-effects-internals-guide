"""Offline host stream resolution path: compare generic/effect/vector identity.
Reads installed BEE PE code only; never loads host modules into the tool.
"""
import pefile,hashlib,json,bisect
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
files={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
       "2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
targets=["?BEE_GetStreamWithSpec@@","?BEE_StreamTypeHasStream@@",
"?BEE_GetEffectIndexFromPath@@","?BEE_IsEffectStreamPath@@",
"?BEE_GetStreamSpecFromLayer@@","?BEE_GetStreamWithSpec"]
r={}
for year,path in files.items():
 blob=Path(path).read_bytes();p=pefile.PE(data=blob);base=p.OPTIONAL_HEADER.ImageBase
 syms={s.address:s.name.decode(errors="replace") for s in p.DIRECTORY_ENTRY_EXPORT.symbols if s.name}
 named={n:next(((ra,si) for ra,si in syms.items() if si.startswith(n)),None) for n in targets}
 pdata=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION)
 begins=[v[0] for v in pdata]
 d=Cs(CS_ARCH_X86,CS_MODE_64);d.detail=True
 methods=[]
 for n in targets[:-1]:
  found=named[n]
  if not found:
   print("NO_SYMBOL",year,n,flush=True);continue
  ra,si=found
  original_entry=ra
  # Follow a short exported near-JMP thunk to the .pdata-covered body.
  thunks=[]
  for _ in range(4):
   ix=bisect.bisect_right(begins,ra)-1
   if ix>=0 and ra<pdata[ix][1]:break
   prefix=list(d.disasm(blob[p.get_offset_from_rva(ra):p.get_offset_from_rva(ra)+32],base+ra))
   # An unwind-less leaf/adjustor thunk can pass new this/path registers
   # before its final unconditional direct JMP.
   jumps=[q for q in prefix if q.mnemonic=='jmp' and q.op_str.startswith('0x') and q.address-base-ra<22]
   if not jumps:break
   jump=jumps[0]
   thunks.append({'rva':hex(ra),'jmp_site':hex(jump.address-base),'target':jump.op_str,
                  'prefix':[t.mnemonic+' '+t.op_str for t in prefix if t.address<=jump.address]})
   ra=int(jump.op_str,16)-base
  ix=bisect.bisect_right(begins,ra)-1
  has_pdata=(ix>=0 and ra<pdata[ix][1])
  end=min(pdata[ix][1],ra+12000) if has_pdata else ra+96
  instructions=[];calls=[]
  for ins in d.disasm(blob[p.get_offset_from_rva(ra):p.get_offset_from_rva(end)],base+ra):
   if len(instructions)<100:instructions.append([hex(ins.address-base),ins.mnemonic,ins.op_str])
   target=None
   if ins.mnemonic in ("call","jmp") and ins.operands:
    op=ins.operands[0]
    if op.type==X86_OP_IMM:target=op.imm-base
    elif op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
     target=ins.address+ins.size+op.mem.disp-base
   if target is not None:
    calls.append({"site":hex(ins.address-base),"destination_rva":hex(target),"symbol":syms.get(target,"")})
  methods.append({"symbol":si,"export_entry":hex(original_entry),"resolved_entry":hex(ra),
                  "thunks":thunks,"has_pdata":has_pdata,"code_end":hex(end),
                  "initial_instructions":instructions,"branches":calls})
  print(year,n,"entry",hex(ra),"direct_edges",len(calls),flush=True)
  for row in calls[:35]:print(" ",row["site"],row["symbol"][:100] or row["destination_rva"],flush=True)
 r[year]={"BEE_sha256":hashlib.sha256(blob).hexdigest(),"methods":methods}
out=Path(r"D:\Developer\ShapeLayerAE\results\native_streamspec_resolver_effect_gate_2025_2026.json")
out.write_text(json.dumps({"classification":"static native BEE stream resolver and effect path identity","versions":r},indent=2)+"\n",encoding="utf8")
print("SAVED",out,flush=True)
