"""Resolve the actual MSVC RTTI class and vtable methods of the native
New Shape Layer command object that BEE's entry-106 handler allocates.
Read only installed AE2025 and 2026 BEE.dll PE bytes.
"""
from pathlib import Path
import pefile,struct,json,hashlib
cfg={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0xfee6e0),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x104eb28)}
out={}
for year,(path,vt_rva) in cfg.items():
 raw=Path(path).read_bytes();p=pefile.PE(data=raw);base=p.OPTIONAL_HEADER.ImageBase
 def u64(rva):return struct.unpack_from("<Q",raw,p.get_offset_from_rva(rva))[0]
 def u32(rva):return struct.unpack_from("<I",raw,p.get_offset_from_rva(rva))[0]
 colptr=u64(vt_rva-8);assert base<=colptr<base+p.OPTIONAL_HEADER.SizeOfImage
 colr=colptr-base
 sig,offs,cdoffs,typerva,hierarchy,selfrva=struct.unpack_from("<IIIIII",raw,p.get_offset_from_rva(colr))
 assert sig==1 and selfrva==colr
 start=p.get_offset_from_rva(typerva+16)
 name=raw[start:start+200].split(b"\x00",1)[0].decode("ascii")
 assert name.startswith(".?AV"),name
 functions=[]
 for slot in range(10):
  ptr=u64(vt_rva+8*slot)
  addr=ptr-base
  if not (base<=ptr<base+p.OPTIONAL_HEADER.SizeOfImage):break
  flags=next((bool(s.Characteristics&0x20000000) for s in p.sections if s.VirtualAddress<=addr<s.VirtualAddress+s.Misc_VirtualSize),False)
  if not flags:break
  functions.append({"slot":slot,"function_rva":hex(addr)})
 out[year]={"sha256":hashlib.sha256(raw).hexdigest(),
   "vtable_rva":hex(vt_rva),"RTTI_COL_rva":hex(colr),"RTTI_type_descriptor_rva":hex(typerva),
   "RTTI_Cpp_class_decorated":name,"RTTI_base_hierarchy_rva":hex(hierarchy),
   "virtual_methods":functions}
 print(year,"CLASS",name,"VTable",hex(vt_rva),"virtuals",functions,flush=True)
p=Path(r"D:\Developer\ShapeLayerAE\results\bee_new_shape_command_object_rtti_vtable_2025_2026.json")
p.write_text(json.dumps({"evidence":"E2-L static native x64 complete-object-locator and MSVC RTTI and executable vtable","versions":out},indent=2)+"\n")
print("SAVED",p)
