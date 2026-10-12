"""Recover BEE_NewLayerTask<4> two concrete native constructors (0x30 bytes)
and field writes/reads to infer native command-owned object layout.
On-disk AE2025/26 BEE only; not a usable third-party ABI.
"""
from pathlib import Path
import pefile,bisect,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
versions={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",[0x5443e0,0x544470]),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",[0x563200,0x563290])}
out={}
for y,(path,entries) in versions.items():
 pe=pefile.PE(path);blob=Path(path).read_bytes();base=pe.OPTIONAL_HEADER.ImageBase
 exp={e.address:e.name.decode(errors="replace") for e in pe.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 imp={i.address:d.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace") for d in pe.DIRECTORY_ENTRY_IMPORT for i in d.imports if i.name}
 pdata=sorted((z.struct.BeginAddress,z.struct.EndAddress) for z in pe.DIRECTORY_ENTRY_EXCEPTION)
 starts=[a for a,b in pdata];dis=Cs(CS_ARCH_X86,CS_MODE_64);dis.detail=True
 paths=[]
 for rva in entries:
  k=bisect.bisect_right(starts,rva)-1
  a,b=pdata[k] if k>=0 and rva<pdata[k][1] else (rva,rva+135)
  ins=[];calls=[]
  for x in dis.disasm(blob[pe.get_offset_from_rva(a):pe.get_offset_from_rva(b)],base+a):
   row={"rva":hex(x.address-base),"ins":x.mnemonic+" "+x.op_str}
   if len(ins)<115:ins.append(row)
   if x.mnemonic not in ("call","jmp") or not x.operands:continue
   arg=x.operands[0];to=None
   if arg.type==X86_OP_IMM:to=arg.imm
   if arg.type==X86_OP_MEM and arg.mem.base==X86_REG_RIP:to=x.address+x.size+arg.mem.disp
   if to is not None:row["target"]=hex(to-base);row["symbol"]=exp.get(to-base) or imp.get(to,"")
   calls.append(row)
  print(y,"TASKCTOR",hex(rva),"size",b-a,flush=True)
  for x in ins[:75]:print(" ",x["rva"],x["ins"],flush=True)
  paths.append({"entry_rva":hex(rva),"data":[hex(a),hex(b)],"instructions":ins,"calls":calls})
 out[y]=paths
p=Path(r"D:\Developer\ShapeLayerAE\results\bee_newshape_task4_native_command_object_constructor_layout_2025_2026.json")
p.write_text(json.dumps({"evidence":"E2-L BEE compiled constructors for 0x30-byte New Shape Layer command task; no native calls executed","versions":out},indent=2)+"\n")
print("SAVED",p)
