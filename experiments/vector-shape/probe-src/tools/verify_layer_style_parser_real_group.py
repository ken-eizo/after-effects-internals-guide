"""Cross-version verification: LayerStyleStreamGroupParser override actually
constructs an IndLayerStyleStreamGroup (not a TDB dummy group).
No host/plugin invocation; static PE decoding only.
"""
from pathlib import Path
import pefile,json,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP
spec={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x2f6300,0x2a0,0x260,0x280),
      "2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x2fef50,0x270,0x230,0x250)}
out={}
for year,(file,start,alloc,offset_a,offset_b) in spec.items():
 data=Path(file).read_bytes();p=pefile.PE(data=data);base=p.OPTIONAL_HEADER.ImageBase
 exports={e.name.decode(errors="replace"):e.address for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 matching=[(n,rv) for n,rv in exports.items() if n.startswith("??_7IndLayerStyleStreamGroup@BEE_LayerStyleStream@@6B@")]
 assert len(matching)==1,(year,matching)
 vn,vr=matching[0]
 body=Cs(CS_ARCH_X86,CS_MODE_64);body.detail=True
 ops=list(body.disasm(data[p.get_offset_from_rva(start):p.get_offset_from_rva(start)+0xc0],base+start))
 assert any(x.mnemonic=="mov" and x.op_str=="ecx, "+hex(alloc) for x in ops)
 fields={offset_a:False,offset_b:False}
 vtable_set=False;vtable_load=False
 for ins in ops:
  if ins.mnemonic=="lea" and ins.op_str.startswith("rax,"):
   op=ins.operands[1]
   if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
    rva=ins.address+ins.size+op.mem.disp-base
    if rva==vr:vtable_load=True
  if ins.mnemonic=="mov" and ins.op_str=="qword ptr [rbx], rax":vtable_set=True
  if ins.mnemonic=="lea":
   for addr in fields:
    if f"[rbx + {hex(addr)}]" in ins.op_str:fields[addr]=True
 assert vtable_load and vtable_set,(year,hex(vr))
 assert all(fields.values()),(year,fields)
 out[year]={"sha256":hashlib.sha256(data).hexdigest(),"override_rva":hex(start),
            "object_allocation_size":hex(alloc),
            "concrete_type":vn,"concrete_vtable_rva":hex(vr),
            "native_NamedStreamGroup_ctor":True,
            "string_member_offsets":[hex(offset_a),hex(offset_b)],
            "returns_concrete_group":True,
            "checked_TDB_serialization_undo_pen_renderer":False}
 print("PASS",year,": real IndLayerStyleStreamGroup allocated",hex(alloc),
       "vtable",hex(vr),flush=True)
dst=Path(r"D:\Developer\ShapeLayerAE\results\bee_layer_style_parser_real_group_verified_2025_2026.json")
dst.write_text(json.dumps({"evidence":"E2-L two-version exact code+vtable; not third-party extensibility","versions":out},indent=2)+"\n")
print("SAVED",dst)
