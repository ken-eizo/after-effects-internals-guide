"""Inspect actual LayerStyleStreamGroupParser::CreateEffectGroup override
found through validated MSVC RTTI descendant vtables, AE 2025/26.
Static native PE, no loading or invocation.
"""
from pathlib import Path
import bisect,json,hashlib
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
versions={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x2f6300),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x2fef50)}
out={}
for year,(file,start) in versions.items():
 data=Path(file).read_bytes();p=pefile.PE(data=data);base=p.OPTIONAL_HEADER.ImageBase
 syms={s.address:s.name.decode(errors="replace") for s in p.DIRECTORY_ENTRY_EXPORT.symbols if s.name}
 imports={s.address:lib.dll.decode(errors="replace")+"!"+s.name.decode(errors="replace")
          for lib in p.DIRECTORY_ENTRY_IMPORT for s in lib.imports if s.name}
 regions=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION)
 i=bisect.bisect_right([v[0] for v in regions],start)-1
 assert i>=0 and regions[i][0]<=start<regions[i][1]
 first,end=regions[i]
 assert end-start<20000,(year,first,end)
 cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
 rows=[];edges=[]
 for ins in cs.disasm(data[p.get_offset_from_rva(start):p.get_offset_from_rva(end)],base+start):
  r={"rva":hex(ins.address-base),"op":ins.mnemonic,"args":ins.op_str}
  target=None
  if ins.mnemonic in ("call","jmp") and ins.operands:
   op=ins.operands[0]
   if op.type==X86_OP_IMM:target=op.imm
   elif op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
    target=ins.address+ins.size+op.mem.disp
  if target is not None:
   r["target"]=hex(target-base)
   r["symbol"]=imports.get(target) or syms.get(target-base,"")
   edges.append(r)
  rows.append(r)
 print(year,"function RVA",hex(start),"end",hex(end),"insns",len(rows),"edges",len(edges),flush=True)
 for r in edges:print("EDGE",r["rva"],r["op"],r.get("symbol") or r.get("target"),flush=True)
 print("FIRST OPS",rows[:55],flush=True)
 out[year]={"BEE_sha256":hashlib.sha256(data).hexdigest(),
            "override_rva":hex(start),"function_end":hex(end),
            "export_name":syms.get(start,""),"instructions":rows,"edges":edges}
dst=Path(r"D:\Developer\ShapeLayerAE\results\bee_layer_style_parser_native_group_constructor_2025_2026.json")
dst.write_text(json.dumps({"classification":"E2-L verified derived RTTI method body, no host invocation","versions":out},indent=2)+"\n")
print("SAVED",dst)
