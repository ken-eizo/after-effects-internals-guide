"""EXP-SHAPE-026 follow generic command adapter target in native BEE owner creation.
Read-only x64 executable machine code for exactly bounded functions.
"""
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_OP_IMM,X86_REG_RIP
import pefile,hashlib,json,subprocess,re,bisect
root=Path(r"D:\Developer\After Effects Internals Guide")
files={"2025":(Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),0x667610),
       "2026":(Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"),0x682f90)}
pattern=re.compile(r"^\s*\d+\s+[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s+(\S+)")
results={}
for ver,(path,entry) in files.items():
 raw=path.read_bytes();p=pefile.PE(data=raw);base=p.OPTIONAL_HEADER.ImageBase
 exports={}
 for ln in subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,errors="replace",check=True).stdout.splitlines():
  m=pattern.match(ln)
  if m:exports[int(m.group(1),16)]=m.group(2)
 imps={obj.address:item.dll.decode(errors="replace")+"!"+obj.name.decode(errors="replace")
       for item in p.DIRECTORY_ENTRY_IMPORT for obj in item.imports if obj.name}
 pdata=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION)
 beginnings=[x[0] for x in pdata]
 cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
 rows=[]
 for address in (entry,0x65cb40 if ver=="2025" else 0x678160):
  ix=bisect.bisect_right(beginnings,address)-1
  start,end=pdata[ix]
  assert start<=address<end
  instructions=[]
  for ins in cs.disasm(raw[p.get_offset_from_rva(start):p.get_offset_from_rva(start)+(end-start)],base+start):
   annotated=""
   if ins.mnemonic in ("call","jmp") and ins.operands:
    op=ins.operands[0];dest=None
    if op.type==X86_OP_IMM:dest=op.imm
    elif op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
     dest=ins.address+ins.size+op.mem.disp
    if dest:
     annotated=exports.get(dest-base) or imps.get(dest) or hex(dest-base)
   instructions.append({"rva":hex(ins.address-base),"mnemonic":ins.mnemonic,
                       "op":ins.op_str,"resolved":annotated})
  rows.append({"target":hex(address),"start":hex(start),"end":hex(end),
               "assembly":instructions})
  print("\n===",ver,"FROM",hex(address),"FUNCTION",hex(start),"len",end-start,flush=True)
  for inst in instructions[:95]:
   print(inst["rva"],inst["mnemonic"],inst["op"],inst["resolved"][:140],flush=True)
 results[ver]={"source_sha256":hashlib.sha256(raw).hexdigest(),"trace":rows}
dest=root/"datasets/ae-native-vector-layer-creation-adapter-target-2025-2026.json"
dest.write_text(json.dumps({"classification":"E2-L static bounded BEE creation code, not third party layer registration",
   "versions":results},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dest,flush=True)
