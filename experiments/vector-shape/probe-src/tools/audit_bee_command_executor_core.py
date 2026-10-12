from pathlib import Path
import bisect,json,pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
cfg={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x64eb80),"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x669840)}
out={}
for year,(path,entry) in cfg.items():
 raw=Path(path).read_bytes();pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase
 ex={e.address:e.name.decode(errors="replace") for e in pe.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 im={i.address:d.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace") for d in pe.DIRECTORY_ENTRY_IMPORT for i in d.imports if i.name}
 pd=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in pe.DIRECTORY_ENTRY_EXCEPTION)
 starts=[a for a,b in pd];k=bisect.bisect_right(starts,entry)-1
 assert k>=0 and entry<pd[k][1]
 a,b=pd[k];cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True;calls=[];instr=[]
 for x in cs.disasm(raw[pe.get_offset_from_rva(a):pe.get_offset_from_rva(b)],base+a):
  r={"rva":hex(x.address-base),"ins":x.mnemonic+" "+x.op_str}
  instr.append(r)
  if x.mnemonic not in ("call","jmp") or not x.operands:continue
  p=x.operands[0];target=None
  if p.type==X86_OP_IMM:target=p.imm
  elif p.type==X86_OP_MEM and p.mem.base==X86_REG_RIP:target=x.address+x.size+p.mem.disp
  if target is not None:r["resolved"]=ex.get(target-base) or im.get(target,"");r["target"]=hex(target-base)
  calls.append(r)
 print(year,hex(a),hex(b),"calls",len(calls),flush=True)
 for r in calls[:55]:print(" ",r,flush=True)
 out[year]={"range":[hex(a),hex(b)],"ins":instr,"calls":calls}
dst=Path(r"D:\Developer\ShapeLayerAE\results\bee_command_executor_dispatch_core_2025_2026.json")
dst.write_text(json.dumps({"evidence":"BEE DoCommand internal executor static disassembly","versions":out},indent=2)+"\n")
print("SAVED",dst)
