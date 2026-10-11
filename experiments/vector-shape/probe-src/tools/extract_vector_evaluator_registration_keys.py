"""Derive the 20 native vector evaluator registration callsites and MatchName-global addresses.
x64 .text disassembly only, no Adobe code execution or project mutation.
"""
from pathlib import Path
import pefile,json,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP,X86_OP_IMM
config={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x6fd400,0x6fe260,0x6eeb20),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x720f20,0x721d5d,0x713120)}
data={}
for ver,(path,begin,end,registrar) in config.items():
 p=pefile.PE(path);raw=Path(path).read_bytes();base=p.OPTIONAL_HEADER.ImageBase
 d=Cs(CS_ARCH_X86,CS_MODE_64);d.detail=True
 instr=list(d.disasm(raw[p.get_offset_from_rva(begin):p.get_offset_from_rva(begin)+(end-begin)],base+begin))
 registers=[]
 for i,x in enumerate(instr):
  if x.mnemonic!="call" or not x.operands or x.operands[0].type!=X86_OP_IMM or x.operands[0].imm-base!=registrar:continue
  near=instr[max(i-11,0):i]
  match_reg=None
  for k in reversed(near):
   if k.mnemonic!="lea" or len(k.operands)!=2 or "rdx" not in k.op_str.split(",")[0]:continue
   src=k.operands[1]
   if src.type==X86_OP_MEM and src.mem.base==X86_REG_RIP:
    match_reg={"instruction_rva":hex(k.address-base),"static_matchname_object_rva":hex(k.address+k.size+src.mem.disp-base)}
    break
  registers.append({"registrar_call_rva":hex(x.address-base),"matchname":match_reg})
 data[ver]={"BEE_sha256":hashlib.sha256(raw).hexdigest(),"registrar_rva":hex(registrar),
            "registration_site_count":len(registers),"records":registers}
 print(ver,"reg count",len(registers),"with match name",sum(bool(x["matchname"]) for x in registers),flush=True)
 for x in registers:print(" ",x["registrar_call_rva"],x["matchname"],flush=True)
dst=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-native-vector-evaluator-registration-records-2025-2026.json")
dst.write_text(json.dumps({"classification":"E2-L static registrar call + operand references only; matchname globals not evaluated","versions":data},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dst)
