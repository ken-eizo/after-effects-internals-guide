"""Resolve CanStore's initial special MatchName using the native global
TDB_MatchName initializer, for actual 2025/2026 installed BEE.dll.
Static only, no private call.
"""
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP
import pefile,json,hashlib
cfg={
"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x1c030,0x700263),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x1b760,0x723c89)}
result={}
for y,(name,ctor,canstore_special) in cfg.items():
 raw=Path(name).read_bytes();pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
 cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
 ins=list(cs.disasm(raw[pe.get_offset_from_rva(ctor):pe.get_offset_from_rva(ctor)+24],base+ctor))
 def rip_target(i):
  for operand in i.operands:
   if operand.type==X86_OP_MEM and operand.mem.base==X86_REG_RIP:
    return i.address+i.size+operand.mem.disp-base
  return None
 lea=[i for i in ins if i.mnemonic=="lea"]
 assert len(lea)>=2,(y,[(i.mnemonic,i.op_str) for i in ins])
 assert lea[0].op_str.startswith("rdx,") and lea[1].op_str.startswith("rcx,"),y
 literalptr=rip_target(lea[0]);objptr=rip_target(lea[1])
 txt=raw[pe.get_offset_from_rva(literalptr):pe.get_offset_from_rva(literalptr)+55].split(b"\x00")[0].decode("ascii")
 assert txt=="ADBE Vector Group",(y,txt)
 first=list(cs.disasm(raw[pe.get_offset_from_rva(canstore_special):pe.get_offset_from_rva(canstore_special)+7],base+canstore_special))[0]
 assert first.mnemonic=="lea" and first.op_str.startswith("rdx,")
 assert rip_target(first)==objptr,(y,hex(rip_target(first)),hex(objptr))
 # Global MatchName obj consumed by CanStore is exactly the object constructed from the native literal.
 result[y]={"BEE_sha256":hashlib.sha256(raw).hexdigest(),"initial_special_case":"ADBE Vector Group",
 "static_TDB_MatchName_constructor_rva":hex(ctor),"literal_rva":hex(literalptr),
 "constructed_global_MatchName_object_rva":hex(objptr),"CanStore_special_comparison_ref_rva":hex(canstore_special),
 "CanStore_references_same_global":True,
 "complete_class_specific_predicate":"name == 'ADBE Vector Group' OR name.startswith('ADBE Vector Shape -') OR name.startswith('ADBE Vector Graphic -') OR name.startswith('ADBE Vector Filter -')",
 "TDB_factory_or_renderer_test_in_predicate":False}
 print("PASS",y,"exact native special child MatchName",txt,"global",hex(objptr),flush=True)
dest=Path(r"D:\Developer\ShapeLayerAE\results\chape_native_canstore_special_exact_matchname_2025_2026.json")
dest.write_text(json.dumps({"evidence":"E2-L x64 constructor literal mapped to exact CanStore global object reference","versions":result},indent=2)+"\n")
print("SAVED",dest)
