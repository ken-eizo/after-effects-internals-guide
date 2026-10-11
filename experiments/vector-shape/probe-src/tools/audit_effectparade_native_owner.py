"""Read-only PE audit: EffectParade native hierarchy ownership and Creator provenance.
Tracks native constructors/Create/Clone and direct CALL targets across AE versions.
"""
from pathlib import Path
import hashlib,json,bisect,pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
files={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
"2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
targets=("?Create@BEE_EffectParade@@","??0BEE_EffectParade@@","?CloneStream@BEE_EffectParade@@",
         "?RegisterStreams@BEE_AVLayer@@")
result={}
for year,path in files.items():
 raw=Path(path).read_bytes();p=pefile.PE(data=raw);base=p.OPTIONAL_HEADER.ImageBase
 ex={s.address:s.name.decode(errors="replace") for s in p.DIRECTORY_ENTRY_EXPORT.symbols if s.name}
 fs=sorted((f.struct.BeginAddress,f.struct.EndAddress) for f in p.DIRECTORY_ENTRY_EXCEPTION)
 beg=[a for a,b in fs]
 imp={e.address:m.dll.decode(errors="replace")+"!"+e.name.decode(errors="replace")
      for m in p.DIRECTORY_ENTRY_IMPORT for e in m.imports if e.name}
 dec=Cs(CS_ARCH_X86,CS_MODE_64);dec.detail=True
 functions=[]
 for a,name in ex.items():
  if not any(name.startswith(t) for t in targets):continue
  ix=bisect.bisect_right(beg,a)-1
  if ix<0 or a>=fs[ix][1]:continue
  n=min(fs[ix][1]-a,10000)
  calls=[];prolog=[]
  for x in dec.disasm(raw[p.get_offset_from_rva(a):p.get_offset_from_rva(a)+n],base+a):
   if len(prolog)<40:prolog.append({"rva":hex(x.address-base),"op":x.mnemonic,"args":x.op_str})
   if x.mnemonic not in ("call","jmp") or not x.operands:continue
   op=x.operands[0];target=None
   if op.type==X86_OP_IMM:target=op.imm-base
   elif op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
    target=x.address+x.size+op.mem.disp-base
   if target is None:continue
   calls.append({"site":hex(x.address-base),"target":hex(target),
                 "export":ex.get(target,""),"import":imp.get(target+base,"")})
  functions.append({"symbol":name,"rva":hex(a),"pdata_end":hex(fs[ix][1]),
                    "first":prolog,"calls":calls})
  print(year,name.split("@")[0],hex(a),"calls",len(calls),flush=True)
  for c in calls[:15]:print(" ",c["site"],(c["export"] or c["import"])[:120] or c["target"],flush=True)
 result[year]={"sha256":hashlib.sha256(raw).hexdigest(),"functions":functions}
dst=Path(r"D:\Developer\ShapeLayerAE\results\effectparade_native_owner_factory_trace_2025_2026.json")
dst.write_text(json.dumps({"evidence":"static PE, not evidence that a PF effect may add native indexed child streams",
"versions":result},indent=2)+"\n",encoding="utf8")
print("SAVED",dst)
