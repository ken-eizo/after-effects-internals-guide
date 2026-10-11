"""Static contract of BEE DynamicStreamEffectsParser creation hooks, both hosts.
Shows which methods are real and whether base CreateEffectGroup constructs an
object or returns nullptr. No private API execution.
"""
from pathlib import Path
import pefile,hashlib,json,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_OP_IMM,X86_REG_RIP
files={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
"2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
patterns=("?CreateEffectGroup@DynamicStreamEffectsParser@",
          "?GetStreamFactory@DynamicStreamEffectsParser@",
          "?ParameterMatchNameFromExternalID@DynamicStreamEffectsParser@",
          "?StartEffect@DynamicStreamEffectsParser@")
result={}
for year,f in files.items():
 b=Path(f).read_bytes();p=pefile.PE(data=b);base=p.OPTIONAL_HEADER.ImageBase
 symbols={e.name.decode(errors="replace"):e.address for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 imps={e.address:lib.dll.decode(errors="replace")+"!"+e.name.decode(errors="replace")
       for lib in p.DIRECTORY_ENTRY_IMPORT for e in lib.imports if e.name}
 md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
 found={}
 for prefix in patterns:
  candidates=[(n,r) for n,r in symbols.items() if n.startswith(prefix)]
  assert len(candidates)<=1,(year,prefix,candidates)
  if not candidates:
   found[prefix]={"exported":False,"reason":"no matching PE export (possible inline/nonexported method)"}
   print(year,prefix.split('@')[0],"NOT EXPORTED",flush=True)
   continue
  name,rva=candidates[0];addr=base+rva
  view=b[p.get_offset_from_rva(rva):][:110]
  rows=[]
  for i in md.disasm(view,addr):
   target=None
   if i.mnemonic in ("call","jmp") and i.operands:
    op=i.operands[0]
    if op.type==X86_OP_IMM:target=op.imm
    if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
     target=i.address+i.size+op.mem.disp
   rows.append({"rva":hex(i.address-base),"mnemonic":i.mnemonic,
                "args":i.op_str,"target_import":imps.get(target,"") if target else "",
                "target_export":next((n for n,r in symbols.items() if base+r==target),"") if target else ""})
   if i.mnemonic=="ret" or len(rows)>=25:break
  found[prefix]={"entry":hex(rva),"instructions":rows,"exact_export":name}
  print(year,prefix.split("@")[0],hex(rva),rows[:7],flush=True)
 group=found[patterns[0]]["instructions"]
 assert group[0]["mnemonic"]=="xor" and group[0]["args"]=="eax, eax"
 assert group[1]["mnemonic"]=="ret"
 result[year]={"sha256":hashlib.sha256(b).hexdigest(),"methods":found,
               "base_CreateEffectGroup_returns_null":True,
               "derived_virtual_override_possibility":"unresolved, requires vtable caller/RTTI audit"}
dest=Path(r"D:\Developer\ShapeLayerAE\results\bee_dynamic_effect_parser_factory_hooks_2025_2026.json")
dest.write_text(json.dumps({"classification":"E2-L exported body machine-code; no actual plugin implementation","years":result},indent=2)+"\n")
print("SAVED",dest)
