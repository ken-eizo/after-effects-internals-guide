"""Inspect the shared NewLayer command tail called by CmdNewVectorLayer.
Native exported path; cross-check 2025 and 2026. No private call.
"""
from pathlib import Path
import bisect,pefile,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
cfg={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x667610),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x682f90)}
out={}
for year,(path,rva) in cfg.items():
 p=pefile.PE(path);data=Path(path).read_bytes();base=p.OPTIONAL_HEADER.ImageBase
 symbols={e.address:e.name.decode(errors="replace") for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 imp={i.address:m.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace") for m in p.DIRECTORY_ENTRY_IMPORT for i in m.imports if i.name}
 pdata=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION);starts=[x[0] for x in pdata]
 k=bisect.bisect_right(starts,rva)-1;a,b=pdata[k] if k>=0 and rva<pdata[k][1] else (rva,rva+180)
 cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True;calls=[];code=[]
 for ins in cs.disasm(data[p.get_offset_from_rva(a):p.get_offset_from_rva(b)],base+a):
  v={"at":hex(ins.address-base),"asm":ins.mnemonic+" "+ins.op_str}
  if len(code)<90:code.append(v)
  if ins.mnemonic in ("call","jmp") and ins.operands:
   arg=ins.operands[0];dst=None
   if arg.type==X86_OP_IMM:dst=arg.imm
   if arg.type==X86_OP_MEM and arg.mem.base==X86_REG_RIP:dst=ins.address+ins.size+arg.mem.disp
   if dst is not None:v["dst_rva"]=hex(dst-base);v["export"]=symbols.get(dst-base) or imp.get(dst,"")
   calls.append(v)
 out[year]={"function_range":[hex(a),hex(b)],"calls":calls,"first_90":code}
 print(year,"shared new-layer worker",hex(rva),"bytes",b-a,"calls",len(calls),flush=True)
 for item in calls[:55]:print(" ",item,flush=True)
target=Path(r"D:\Developer\ShapeLayerAE\results\bee_new_shape_shared_newlayer_worker_2025_2026.json")
target.write_text(json.dumps({"evidence":"E2-L native BEE CmdNewVectorLayer forwarding to shared new-layer routine, static bounded disassembly only","versions":out},indent=2)+"\n")
print("SAVED",target)
