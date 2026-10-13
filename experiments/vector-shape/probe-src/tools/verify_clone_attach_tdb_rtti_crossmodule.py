"""Resolve RTTI type descriptors in BEE_Layer::CloneAndAttach's dynamic_cast,
verified by both installed native BEE.dll binaries and TDB StreamBase::Clone IAT.
Offline; no private APIs are executed.
"""
from pathlib import Path
import pefile,json,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP,X86_OP_IMM
cfg={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x2e20e0,0x2e218f),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x2eb090,0x2eb140)}
out={}
for year,(path,entry,attachsite) in cfg.items():
 blob=Path(path).read_bytes();p=pefile.PE(data=blob,fast_load=True)
 p.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"],pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXPORT"]])
 b=p.OPTIONAL_HEADER.ImageBase
 dec=Cs(CS_ARCH_X86,CS_MODE_64);dec.detail=True
 ins=list(dec.disasm(blob[p.get_offset_from_rva(entry):p.get_offset_from_rva(entry)+235],b+entry))
 cast=next(i for i in ins if i.mnemonic=="call" and i.operands and i.operands[0].type==X86_OP_IMM
  and i.operands[0].imm-b>0xc00000 and i.operands[0].imm-b<0xe00000)
 idx=ins.index(cast)
 prev=ins[max(0,idx-7):idx]
 tp={}
 for i in prev:
  if i.mnemonic!="lea" or len(i.operands)<2:continue
  op=i.operands[1]
  if op.type!=X86_OP_MEM or op.mem.base!=X86_REG_RIP:continue
  if i.operands[0].reg not in (104,105):continue # don't rely on these numeric REG IDs; use reg_name below
  # no-op
 for i in prev:
  if i.mnemonic!="lea" or len(i.operands)<2:continue
  op=i.operands[1]
  if op.type!=X86_OP_MEM or op.mem.base!=X86_REG_RIP:continue
  reg=i.reg_name(i.operands[0].reg)
  if reg not in ("r8","r9"):continue
  target=i.address+i.size+op.mem.disp-b
  rawname=blob[p.get_offset_from_rva(target)+16:p.get_offset_from_rva(target)+128].split(b"\x00")[0].decode("ascii",errors="replace")
  tp[reg]={"descriptor_rva":hex(target),"RTTI_decorated":rawname}
 assert "r8" in tp and "r9" in tp,(year,tp)
 assert "TDB_StreamBase" in tp["r8"]["RTTI_decorated"],tp
 assert "BEE_Layer" in tp["r9"]["RTTI_decorated"],tp
 calls=[i for i in ins if i.address-b==attachsite]
 assert len(calls)==1 and calls[0].mnemonic=="call"
 earlier=ins[:idx]
 clone=[i for i in earlier if i.mnemonic=="call" and i.operands and i.operands[0].type==X86_OP_MEM and i.operands[0].mem.base==X86_REG_RIP]
 assert len(clone)==1,(year,clone)
 i=clone[0]
 import_rva=i.address+i.size+i.operands[0].mem.disp-b
 lookup={}
 for lib in p.DIRECTORY_ENTRY_IMPORT:
  for sym in lib.imports:
   if sym.name and sym.address-b==import_rva:lookup={"dll":lib.dll.decode(),"name":sym.name.decode()}
 assert lookup=={"dll":"TDB.dll","name":"?Clone@TDB_StreamBase@@UEBAPEAV1@_N@Z"},(year,lookup)
 out[year]={"BEE_SHA256":hashlib.sha256(blob).hexdigest(),
 "BEE_Layer_CloneAndAttach_rva":hex(entry),
 "TDB_StreamBase_virtual_clone_IAT":hex(import_rva),
 "clone_symbol":lookup,
 "RTDynamicCast_thunk":hex(cast.operands[0].imm-b),
 "dynamic_cast_src_type":tp["r8"],
 "dynamic_cast_target_type":tp["r9"],
 "BEE_CompItem_attachment_callsite":hex(attachsite),
 "clone_then_cast_then_attach":True,
 "BEE_native_new_class_registered":False}
 print("PASS",year,"TDB Clone -> dynamic_cast from",tp["r8"]["RTTI_decorated"],"to",tp["r9"]["RTTI_decorated"],"-> Comp attach",flush=True)
dest=Path(r"D:\Developer\ShapeLayerAE\results\bee_clone_attach_tdb_stream_rtti_owner_boundary_2025_2026.json")
dest.write_text(json.dumps({"evidence":"E2-L exact installed native x64 calls, RTTI descriptors, TDB DLL import; static only","versions":out},indent=2)+"\n")
print("SAVED",dest)
