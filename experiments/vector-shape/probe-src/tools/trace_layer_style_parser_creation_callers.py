"""Trace actual native LayerStyleStreamGroupParser construction callers
and their TDB/FLT/parse dependencies in AE2025/2026.
Static PE disassembly only; no host execution.
"""
from pathlib import Path
import json,hashlib,pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
cfg={
"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",[(0x2f35d0,0x2f365a),(0x2fbb60,0x2fc0c0)]),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",[(0x2fc370,0x2fc401),(0x304640,0x304bad)])}
out={}
for year,(filename,spans) in cfg.items():
 raw=Path(filename).read_bytes();p=pefile.PE(data=raw);base=p.OPTIONAL_HEADER.ImageBase
 symbols={s.address:s.name.decode(errors="replace") for s in p.DIRECTORY_ENTRY_EXPORT.symbols if s.name}
 imports={s.address:lib.dll.decode(errors="replace")+"!"+s.name.decode(errors="replace")
          for lib in p.DIRECTORY_ENTRY_IMPORT for s in lib.imports if s.name}
 cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
 routines=[]
 for begin,end in spans:
  rows=[];edges=[]
  for x in cs.disasm(raw[p.get_offset_from_rva(begin):p.get_offset_from_rva(end)],base+begin):
   r={"rva":hex(x.address-base),"op":x.mnemonic,"args":x.op_str}
   if x.mnemonic in ("call","jmp") and x.operands:
    target=None;opr=x.operands[0]
    if opr.type==X86_OP_IMM:target=opr.imm
    elif opr.type==X86_OP_MEM and opr.mem.base==X86_REG_RIP:
     target=x.address+x.size+opr.mem.disp
    if target is not None:
     r["target"]=hex(target-base)
     r["symbol"]=imports.get(target) or symbols.get(target-base,"")
     edges.append(r)
   rows.append(r)
  routines.append({"begin":hex(begin),"end":hex(end),"instructions":rows,"edges":edges})
  print("YEAR",year,"FUNCTION",hex(begin),"CALLS",len(edges),flush=True)
  for e in edges:
   print(" ",e["rva"],e.get("symbol") or e.get("target"),flush=True)
 out[year]={"sha256":hashlib.sha256(raw).hexdigest(),"routines":routines}
dst=Path(r"D:\Developer\ShapeLayerAE\results\bee_layer_style_parser_creation_callers_2025_2026.json")
dst.write_text(json.dumps({"evidence":"native RTTI-vtable constructor xrefs, bounded PE disassembly","versions":out},indent=2)+"\n")
print("SAVED",dst)
