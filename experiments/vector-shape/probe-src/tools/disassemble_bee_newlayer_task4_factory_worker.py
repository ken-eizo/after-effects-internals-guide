"""Disassemble the real BEE_NewLayerTask<4>::Execute allocation function:
0x3151d0 2025 / 0x31e800 2026, on-disk native PE only.
"""
from pathlib import Path
import json,pefile,bisect
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_OP_IMM,X86_REG_RIP
cfg={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x3151d0),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x31e800)}
out={}
for y,(path,target) in cfg.items():
 p=pefile.PE(path);raw=Path(path).read_bytes();base=p.OPTIONAL_HEADER.ImageBase
 exports={e.address:e.name.decode(errors="replace") for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 imp={i.address:desc.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace") for desc in p.DIRECTORY_ENTRY_IMPORT for i in desc.imports if i.name}
 pdata=sorted((i.struct.BeginAddress,i.struct.EndAddress) for i in p.DIRECTORY_ENTRY_EXCEPTION);starts=[x[0] for x in pdata]
 k=bisect.bisect_right(starts,target)-1;a,b=pdata[k] if k>=0 and target<pdata[k][1] else (target,target+120)
 cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
 instr=[];calls=[]
 for i in cs.disasm(raw[p.get_offset_from_rva(a):p.get_offset_from_rva(b)],base+a):
  row={"rva":hex(i.address-base),"ins":i.mnemonic+" "+i.op_str}
  if len(instr)<120:instr.append(row)
  if i.mnemonic not in ("call","jmp") or not i.operands:continue
  q=i.operands[0];to=None
  if q.type==X86_OP_IMM:to=q.imm
  if q.type==X86_OP_MEM and q.mem.base==X86_REG_RIP:to=i.address+i.size+q.mem.disp
  if to is not None:row["to_rva"]=hex(to-base);row["symbol"]=exports.get(to-base) or imp.get(to,"")
  calls.append(row)
 print(y,"REAL_NEW_LAYER_WORKER",hex(a),hex(b),"bytes",b-a,"calls",len(calls),flush=True)
 for x in calls:print(" ",x,flush=True)
 out[y]={"entry_rva":hex(target),"range":[hex(a),hex(b)],"calls":calls,"first_instructions":instr}
dst=Path(r"D:\Developer\ShapeLayerAE\results\bee_real_newlayer_task4_factory_worker_2025_2026.json")
dst.write_text(json.dumps({"evidence":"E2-L disassembly of BEE_NewLayerTask<4> slot1 direct worker; real compiled code","versions":out},indent=2)+"\n")
print("SAVED",dst)
