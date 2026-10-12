"""Audit matched methods called by native BEE_CompItem::AttachLayerToCompOnly
in AE2025/26, using bounded function disassembly and callsite arguments.
All offline, no Adobe process. Emits compact information only.
"""
import json,bisect,pefile,hashlib
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
links={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
 {"primary_placement":0x39a550,"id_check":0x38ed70,"track_state":0x318f20,"flag_write":0x312ce0,
  "eligibility_comp":0x39a3d0,"owner_initialization":0x2ecd20}),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",
 {"primary_placement":0x3a5830,"id_check":0x39a1c0,"track_state":0x322450,"flag_write":0x31c280,
  "eligibility_comp":0x3a56b0,"owner_initialization":0x2f57e0})}
out={}
for y,(file,functions) in links.items():
 raw=Path(file).read_bytes();p=pefile.PE(data=raw);base=p.OPTIONAL_HEADER.ImageBase
 pd=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION);starts=[a for a,b in pd]
 exports={e.address:e.name.decode(errors="replace") for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 imports={i.address:z.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace") for z in p.DIRECTORY_ENTRY_IMPORT for i in z.imports if i.name}
 dis=Cs(CS_ARCH_X86,CS_MODE_64);dis.detail=True
 rows={}
 for role,rva in functions.items():
  k=bisect.bisect_right(starts,rva)-1
  if k>=0 and rva<pd[k][1]:a,b=pd[k]
  else:a,b=rva,rva+96 # no pdata leaf: bound narrow static scan
  instructions=list(dis.disasm(raw[p.get_offset_from_rva(a):p.get_offset_from_rva(b)],base+a))
  calls=[];writes=[]
  for x in instructions:
   if x.mnemonic in ("call","jmp") and x.operands:
    op=x.operands[0];dst=None
    if op.type==X86_OP_IMM:dst=op.imm
    if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:dst=x.address+x.size+op.mem.disp
    if dst is not None:
     calls.append({"site":hex(x.address-base),"dst":hex(dst-base),
        "symbol":imports.get(dst) or exports.get(dst-base,"")})
   if x.mnemonic in ("mov","movups","movaps","add","sub","inc","xadd","cmpxchg","lock") and x.operands and x.operands[0].type==X86_OP_MEM:
    writes.append({"at":hex(x.address-base),"ins":x.mnemonic+" "+x.op_str})
  rows[role]={"start":hex(a),"end":hex(b),"byte_count":b-a,"calls":calls,
   "writes_first_60":writes[:60], "near_export":exports.get(a,"")}
  print(y,role,"rva",hex(rva),"function_bytes",b-a,"calls",len(calls),"memwrite",len(writes),flush=True)
  if role=="primary_placement":
   for x in calls[:35]:print("   ",x,flush=True)
   print("   writes:",writes[:25],flush=True)
 out[y]={"SHA256":hashlib.sha256(raw).hexdigest(),"attach_callees":rows}
target=Path(r"D:\Developer\ShapeLayerAE\results\bee_comp_layer_attach_side_effect_helpers_2025_2026.json")
target.write_text(json.dumps({"evidence":"E2-L 2025/2026 BEE native bounded code of helpers directly called by CompItem::AttachLayerToCompOnly","versions":out},indent=2)+"\n")
print("SAVED",target)
