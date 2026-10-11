"""Static AE2025/26 BEE native Layer factory dispatch audit.
Find actual type admission and native creator call sites; never invoke host APIs.
"""
import pefile,hashlib,json,bisect
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
files={
"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
"2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
report={}
for year,file in files.items():
 raw=Path(file).read_bytes();pe=pefile.PE(data=raw)
 base=pe.OPTIONAL_HEADER.ImageBase
 named={s.address:s.name.decode(errors="replace") for s in pe.DIRECTORY_ENTRY_EXPORT.symbols if s.name}
 found=[(r,n) for r,n in named.items() if n.startswith("?CreateLayerFromType@BEE_Layer@@")]
 assert len(found)==1
 rva,name=found[0]
 fs=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in pe.DIRECTORY_ENTRY_EXCEPTION)
 start=[a for a,b in fs]
 index=bisect.bisect_right(start,rva)-1
 assert index>=0 and rva<fs[index][1]
 first,last=fs[index];assert last-first<12000,(year,first,last)
 code=raw[pe.get_offset_from_rva(first):pe.get_offset_from_rva(first)+(last-first)]
 c=Cs(CS_ARCH_X86,CS_MODE_64);c.detail=True
 operations=[]
 for ins in c.disasm(code,base+first):
  call=None
  if ins.mnemonic in ("call","jmp") and ins.operands:
   op=ins.operands[0]
   if op.type==X86_OP_IMM:call=op.imm-base
   elif op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
    call=ins.address+ins.size+op.mem.disp-base
  operations.append({"rva":hex(ins.address-base),"m":ins.mnemonic,"args":ins.op_str,
   "target":hex(call) if call is not None else None,
   "export":named.get(call,"") if call is not None else ""})
 report[year]={"BEE_sha256":hashlib.sha256(raw).hexdigest(),"factory_export":name,
  "entry_rva":hex(rva),"function_begin":hex(first),"function_end":hex(last),
  "instructions":operations}
 print("=== YEAR",year,"FUNCTION",hex(first),hex(last),"OPS",len(operations),flush=True)
 for x in operations:
  if x["m"] in ("cmp","test","call","jmp","movzx","sub") and (len(operations)<240 or x["m"] in ("call","jmp")):
   print(x["rva"],x["m"],x["args"],x["export"][:110],flush=True)
path=Path(r"D:\Developer\ShapeLayerAE\results\native_layer_factory_type_dispatch_2025_2026.json")
path.write_text(json.dumps({"classification":"static native BEE compiled layer construction only; no proof of external subclass extension","versions":report},indent=2)+"\n",encoding="utf8")
print("SAVED",path,flush=True)
