"""Read-only native FLT_FCSeqSpec canonical parameter/UI-layout call graph.
Both pinned FLT.dll binaries; machine code not executed.
"""
from pathlib import Path
import json,bisect,hashlib,pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
files={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\FLT.dll",
"2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\FLT.dll"}
need=("?FillInCanonicalUILayout@FLT_FCSeqSpec@@","?AddStreamToUILayout@FLT_FCSeqSpec@@",
"?GetChildParamDef@FLT_FCSeqSpec@@","?GetParamTable@FLT_FCSeqSpec@@")
out={}
for year,fn in files.items():
 raw=Path(fn).read_bytes();p=pefile.PE(data=raw);base=p.OPTIONAL_HEADER.ImageBase
 exports={e.address:e.name.decode(errors="replace") for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 imports={i.address:e.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace")
          for e in p.DIRECTORY_ENTRY_IMPORT for i in e.imports if i.name}
 pdata=sorted((f.struct.BeginAddress,f.struct.EndAddress) for f in p.DIRECTORY_ENTRY_EXCEPTION)
 b=[f[0] for f in pdata];md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
 funcs=[]
 for rva,n in exports.items():
  if not any(n.startswith(k) for k in need):continue
  ix=bisect.bisect_right(b,rva)-1
  # A few optimized tiny exported routines have no unwind/pdata record.
  # Bound those to 128 bytes; never scan unrelated large adjacent regions.
  has_unwind=ix>=0 and rva<pdata[ix][1]
  stop=min(pdata[ix][1],rva+12000) if has_unwind else rva+128
  calls=[];first=[]
  for ins in md.disasm(raw[p.get_offset_from_rva(rva):p.get_offset_from_rva(stop)],base+rva):
   if not has_unwind and ins.mnemonic=="int3":break
   if len(first)<50:first.append({"rva":hex(ins.address-base),"mnemonic":ins.mnemonic,"operands":ins.op_str})
   if ins.mnemonic not in ("call","jmp") or not ins.operands:continue
   op=ins.operands[0];target=None
   if op.type==X86_OP_IMM:target=op.imm
   if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:target=ins.address+ins.size+op.mem.disp
   if target:
    calls.append({"site":hex(ins.address-base),"rva":hex(target-base),
     "name":exports.get(target-base,"") or imports.get(target,"")})
  funcs.append({"symbol":n,"rva":hex(rva),"calls":calls,"prologue":first})
  print(year,n.split("@")[0],hex(rva),"calls",len(calls),flush=True)
  for c in calls[:28]:print(" ",c["site"],c["name"][:115] or c["rva"],flush=True)
 out[year]={"sha256":hashlib.sha256(raw).hexdigest(),"functions":funcs}
dst=Path(r"D:\Developer\ShapeLayerAE\results\flt_effect_canonical_layout_builder_2025_2026.json")
dst.write_text(json.dumps({"evidence":"E2-L installed native FLT static instructions; not permission to add arbitrary PF child","versions":out},indent=2)+"\n")
print("SAVED",dst)
