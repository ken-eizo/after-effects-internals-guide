"""Resolve eleven temporary LayerStyle TDB creator callbacks to concrete
vtable classes and native constructor edges, AE2025 and AE2026. Read only.
"""
from pathlib import Path
import pefile,json,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_OP_IMM,X86_REG_RIP
source=Path(r"D:\Developer\ShapeLayerAE\results\layer_style_scoped_registered_type_sources_2025_2026.json")
original=json.loads(source.read_text())["versions"]
files={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
       "2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
results={}
for year,path in files.items():
 b=Path(path).read_bytes();p=pefile.PE(data=b);base=p.OPTIONAL_HEADER.ImageBase
 exports={e.address:e.name.decode(errors="replace") for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 import_map={i.address:desc.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace")
         for desc in p.DIRECTORY_ENTRY_IMPORT for i in desc.imports if i.name}
 decoder=Cs(CS_ARCH_X86,CS_MODE_64);decoder.detail=True
 rows=[]
 for row in original[year]["registration_calls"]:
  candidates=[x for x in row["rip_sources"] if x["dest"]=="rax"]
  assert len(candidates)==1,(year,row)
  at=int(candidates[0]["target_rva"],16)
  seq=list(decoder.disasm(b[p.get_offset_from_rva(at):p.get_offset_from_rva(at)+420],base+at))
  allocs=[];vtables=[];edges=[]
  for idx,ins in enumerate(seq):
   if ins.mnemonic=="mov" and ins.op_str.startswith("ecx, 0x"):allocs.append(ins.op_str)
   if ins.mnemonic=="lea" and ins.operands:
    arg=ins.operands[-1]
    if arg.type==X86_OP_MEM and arg.mem.base==X86_REG_RIP:
     rr=ins.address+ins.size+arg.mem.disp-base
     name=exports.get(rr,"")
     if name.startswith("??_7"):
      vtables.append({"rva":hex(rr),"class_vtable":name,"site":hex(ins.address-base)})
   if ins.mnemonic in ("call","jmp") and ins.operands:
    op=ins.operands[0]
    target=None
    if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:target=ins.address+ins.size+op.mem.disp
    elif op.type==X86_OP_IMM:target=op.imm
    if target:
     sym=exports.get(target-base) or import_map.get(target,"")
     if sym: edges.append({"site":hex(ins.address-base),"symbol":sym})
   if ins.mnemonic=="ret":break
  rows.append({"register_call":row["callsite"],"callback_rva":hex(at),
      "export_symbol":exports.get(at,""),"allocator_sizes":allocs,
      "vtable_assignments":vtables,"named_call_edges":edges})
 print(year,"CALLBACKS",len(rows),flush=True)
 for i,x in enumerate(rows):
  print(i,x["callback_rva"],"VT",[(v["class_vtable"][:80],v["rva"]) for v in x["vtable_assignments"]],
       "CTOR",[(s["symbol"][:75]) for s in x["named_call_edges"] if "??0" in s["symbol"]],flush=True)
 results[year]={"sha256":hashlib.sha256(b).hexdigest(),"registered_callback_creators":rows}
dst=Path(r"D:\Developer\ShapeLayerAE\results\layerstyle_11_tdb_creators_concrete_classes_2025_2026.json")
dst.write_text(json.dumps({"evidence":"E2-L x64 .text static callback class allocator/vtable resolution, no Adobe calls","years":results},indent=2)+"\n")
print("SAVED",dst)
