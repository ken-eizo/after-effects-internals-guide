"""Verify actual FLT_Parade::CanStore canonical lookup and C++ RTTI admission.
PE-only: exact AE2025/2026 bytes; no native Adobe function execution.
"""
from pathlib import Path
import json,pefile,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_OP_IMM,X86_REG_RIP,X86_REG_R8,X86_REG_R9
inputs={
"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\FLT.dll",
"2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\FLT.dll"}
result={}
for year,fn in inputs.items():
 data=Path(fn).read_bytes();pe=pefile.PE(data=data);base=pe.OPTIONAL_HEADER.ImageBase
 exports={s.name.decode(errors="replace"):s.address for s in pe.DIRECTORY_ENTRY_EXPORT.symbols if s.name}
 names=[(n,r) for n,r in exports.items() if n.startswith("?CanStore@FLT_Parade@@")]
 assert len(names)==1,names
 name,rva=names[0]
 imports={i.address:e.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace")
  for e in pe.DIRECTORY_ENTRY_IMPORT for i in e.imports if i.name}
 dec=Cs(CS_ARCH_X86,CS_MODE_64);dec.detail=True
 def decode(start,num):
  return list(dec.disasm(data[pe.get_offset_from_rva(start):pe.get_offset_from_rva(start)+num],base+start))
 ins=decode(rva,60)
 assert ins[0].mnemonic=="sub"
 matches=[];castcalls=[];types={}
 for x in ins:
  if x.mnemonic=="lea" and len(x.operands)>=2 and x.operands[1].type==X86_OP_MEM:
   if x.operands[1].mem.base==X86_REG_RIP:
    target=x.address+x.size+x.operands[1].mem.disp-base
    txt=data[pe.get_offset_from_rva(target+16):pe.get_offset_from_rva(target+16)+85].split(b"\0",1)[0].decode("ascii","replace")
    if x.operands[0].reg==X86_REG_R8:types["source"]=txt
    if x.operands[0].reg==X86_REG_R9:types["destination"]=txt
  if x.mnemonic=="call" and x.operands[0].type==X86_OP_MEM:
   target=x.address+x.size+x.operands[0].mem.disp
   matches.append(imports.get(target,""))
  if x.mnemonic=="call" and x.operands[0].type==X86_OP_IMM:
   thunk=x.operands[0].imm-base
   thunkins=decode(thunk,6)
   assert len(thunkins)==1 and thunkins[0].mnemonic=="jmp"
   y=thunkins[0];dest=y.address+y.size+y.operands[0].mem.disp
   castcalls.append({"thunk":hex(thunk),"import":imports.get(dest,"")})
 assert len(matches)==1 and "TDB.dll!?GetCanonicalStream@TDB_StreamBase@@" in matches[0],matches
 assert len(castcalls)==1 and castcalls[0]["import"]=="VCRUNTIME140.dll!__RTDynamicCast",castcalls
 assert types=={"source":".?AVTDB_StreamBase@@","destination":".?AVFLT_FCSeqSpec@@"},types
 assert any(x.mnemonic=="test" and x.op_str=="rax, rax" for x in ins)
 assert any(x.mnemonic=="setne" and x.op_str=="al" for x in ins)
 assert any(x.mnemonic=="mov" and "dword ptr [rsp + 0x20], 0" in x.op_str for x in ins)
 result[year]={"sha256":hashlib.sha256(data).hexdigest(),"function":name,"rva":hex(rva),
 "canonical_import":matches[0],"dynamic_cast":castcalls[0],"types":types,
 "return":"CanStore = (dynamic_cast<FLT_FCSeqSpec*>(canonical) != nullptr)",
 "admission_success_proven_in_host":False}
 print("PASS",year,"canonical RTTI admission:",types["source"],"->",types["destination"],flush=True)
dest=Path(r"D:\Developer\ShapeLayerAE\results\flt_parade_canonical_rtti_gate_2025_2026.json")
dest.write_text(json.dumps({"scope":"two pinned native FLT binaries; compiler-level observed RTTI, not external plugin registration","versions":result},indent=2)+"\n")
print("SAVED",dest)
