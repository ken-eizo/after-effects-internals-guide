"""Trace native BEE_DoCommand -> project Undo context -> dynamic command dispatch.
Exact native exports and PDATA, two pinned BEE.dll builds, no invocation.
"""
from pathlib import Path
import bisect,pefile,hashlib,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
versions={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
          "2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
records={}
for v,path in versions.items():
 raw=Path(path).read_bytes();p=pefile.PE(data=raw);base=p.OPTIONAL_HEADER.ImageBase
 exports={e.name.decode(errors="replace"):e.address for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 names={rv:name for name,rv in exports.items()}
 imports={i.address:desc.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace") for desc in p.DIRECTORY_ENTRY_IMPORT for i in desc.imports if i.name}
 pdata=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION)
 starts=[x[0] for x in pdata]
 decoder=Cs(CS_ARCH_X86,CS_MODE_64);decoder.detail=True
 info={}
 for sym,rva in exports.items():
  if not sym.startswith("?BEE_DoCommand@@"):continue
  k=bisect.bisect_right(starts,rva)-1
  a,b=pdata[k] if k>=0 and rva<pdata[k][1] else (rva,rva+120)
  instr=[];call=[]
  for x in decoder.disasm(raw[p.get_offset_from_rva(a):p.get_offset_from_rva(b)],base+a):
   row={"at":hex(x.address-base),"asm":x.mnemonic+" "+x.op_str}
   instr.append(row)
   if x.mnemonic not in ("call","jmp") or not x.operands:continue
   arg=x.operands[0];target=None
   if arg.type==X86_OP_IMM:target=arg.imm
   if arg.type==X86_OP_MEM and arg.mem.base==X86_REG_RIP:target=x.address+x.size+arg.mem.disp
   if target is not None:
    row["target"]=hex(target-base)
    row["symbol"]=names.get(target-base) or imports.get(target,"")
   call.append(row)
  info[sym]={"entry_rva":hex(rva),"pdata":[hex(a),hex(b)],"calls":call,"instructions":instr[:160]}
  print(v,sym,"entry",hex(rva),"size",b-a,flush=True)
  for x in call[:50]:print(" ",x,flush=True)
 records[v]={"BEE_sha256":hashlib.sha256(raw).hexdigest(),"entrypoints":info}
out=Path(r"D:\Developer\ShapeLayerAE\results\bee_command_undo_dispatch_native_internal_2025_2026.json")
out.write_text(json.dumps({"evidence":"E2-L native BEE_DoCommand C++ overloads bounded x64 code, Adobe DLL never executed","versions":records},indent=2)+"\n")
print("SAVED",out)
