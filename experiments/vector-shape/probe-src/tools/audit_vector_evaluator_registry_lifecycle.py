"""Resolve native evaluator-registry global initializer and shutdown routines.
Static .pdata function boundary inspection only.
"""
import pefile,bisect,json,re,subprocess
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
paths={
"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",[0x6eef4a,0x6eefb0,0x6ef08f,0x6f88c4,0x6fdccb]),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",[0x71355a,0x7135b9,0x71369f,0x71c3d4,0x7217cb])}
res={}
for ver,(file,points) in paths.items():
 p=pefile.PE(file);raw=Path(file).read_bytes();base=p.OPTIONAL_HEADER.ImageBase
 iat={i.address:m.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace") for m in p.DIRECTORY_ENTRY_IMPORT for i in m.imports if i.name}
 fs=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in p.DIRECTORY_ENTRY_EXCEPTION)
 starts=[x[0] for x in fs]
 md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
 found={}
 for addr in points:
  idx=bisect.bisect_right(starts,addr)-1
  if idx<0:continue
  a,b=fs[idx]
  if addr>=b:continue
  k=(a,b)
  if k in found:continue
  ops=[];touched=[]
  for ins in md.disasm(raw[p.get_offset_from_rva(a):p.get_offset_from_rva(a)+(b-a)],base+a):
   tar=None
   if ins.operands and ins.mnemonic in ("call","jmp"):
    o=ins.operands[0]
    if o.type==X86_OP_MEM and o.mem.base==X86_REG_RIP:tar=ins.address+ins.size+o.mem.disp
    elif o.type==X86_OP_IMM:tar=o.imm
   label=iat.get(tar,"")
   ops.append({"site":hex(ins.address-base),"op":ins.mnemonic+" "+ins.op_str,
              "import":label,"target_rva":hex(tar-base) if tar is not None else ""})
  found[k]={"function_begin":hex(a),"function_end":hex(b),"bytes":b-a,"instructions":ops}
 res[ver]=list(found.values())
 print("==",ver,flush=True)
 for f in res[ver]:
  print("FUNCTION",f["function_begin"],f["function_end"],"len",f["bytes"],"insns",len(f["instructions"]),flush=True)
  for o in f["instructions"]:
   if "call" in o["op"] or ("0x" in o["op"] and "rip" in o["op"] and o["site"] in [hex(a) for a in points]):
    print("  ",o["site"],o["import"][:110] or o["op"][:105],flush=True)
dest=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-native-vector-evaluator-registry-lifecycle-2025-2026.json")
dest.write_text(json.dumps({"evidence":"E2-L; static, bounded native registry init/cleanup","versions":res},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dest)
