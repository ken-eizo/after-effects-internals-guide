"""Resolve each of BEE VectorLayer's 62 TDB type registrations to native
MatchName exported constants and typed creator function pointer.
Offline installed AE2025 and AE2026 PE images only.
"""
from pathlib import Path
import pefile,hashlib,json,bisect
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP
cfg={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x77c630,0x77d338),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x79d040,0x79dd37)}
allout={}
for ver,(path,a,b) in cfg.items():
 blob=Path(path).read_bytes();p=pefile.PE(data=blob);base=p.OPTIONAL_HEADER.ImageBase
 exports={e.address:e.name.decode(errors="replace") for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 imports={i.address:desc.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace") for desc in p.DIRECTORY_ENTRY_IMPORT for i in desc.imports if i.name}
 md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
 ins=list(md.disasm(blob[p.get_offset_from_rva(a):p.get_offset_from_rva(b)],base+a))
 regs=[];other=[]
 for j,i in enumerate(ins):
  if i.mnemonic!="call" or not i.operands:continue
  op=i.operands[0]
  if op.type!=X86_OP_MEM or op.mem.base!=X86_REG_RIP:continue
  target=i.address+i.size+op.mem.disp
  symbol=imports.get(target,"")
  if "?Register@TDB_ScRegisterStreams@@" not in symbol:continue
  candidates=[]
  for x in ins[max(0,j-14):j]:
   if x.mnemonic!="lea" or len(x.operands)!=2:continue
   right=x.operands[1]
   if right.type!=X86_OP_MEM or right.mem.base!=X86_REG_RIP:continue
   rva=x.address+x.size+right.mem.disp-base
   candidates.append({"reg":x.reg_name(x.operands[0].reg),"data_rva":hex(rva),"symbol":exports.get(rva,""),"site":hex(x.address-base)})
  matchs=[x for x in candidates if x["reg"]=="rdx"]
  creators=[x for x in candidates if x["reg"]=="rax"]
  if not matchs:
   raise RuntimeError((ver,hex(i.address-base),"no MatchName"))
  if not creators:
   # Two adjacent registrations reuse a creator held in RBX instead of
   # materializing a fresh LEA RAX for each callback.
   for x in ins[max(0,j-40):j]:
    if x.mnemonic=="lea" and len(x.operands)==2 and x.reg_name(x.operands[0].reg)=="rbx" and x.operands[1].type==X86_OP_MEM and x.operands[1].mem.base==X86_REG_RIP:
     cr=x.address+x.size+x.operands[1].mem.disp-base
     creators=[{"reg":"rbx","data_rva":hex(cr),"symbol":exports.get(cr,""),"site":hex(x.address-base)}]
  assert creators,(ver,hex(i.address-base),"no creator")
  regs.append({"index":len(regs),"call_rva":hex(i.address-base),"match":matchs[-1],"creator":creators[-1]})
 assert len(regs)==62,(ver,len(regs))
 setup_rva=0x77d2cd if ver=="2025" else 0x79dcda
 sites=[(j,i) for j,i in enumerate(ins) if i.address-base==setup_rva]
 if sites:
  j,site=sites[0]
  neighborhood=ins[j-22:j+11]
 else:
  # Capstone linear sweep may stop early when code and embedded data mix.
  # Start at a known instruction boundary exactly 23 bytes before call.
  off=p.get_offset_from_rva(setup_rva-23)
  neighborhood=list(md.disasm(blob[off:off+90],base+setup_rva-23))
  site=next((x for x in neighborhood if x.address-base==setup_rva),None)
 assert site is not None,(ver,hex(setup_rva))
 around=[]
 for x in neighborhood:
  rv=None
  if len(x.operands)>1 and x.operands[1].type==X86_OP_MEM and x.operands[1].mem.base==X86_REG_RIP:
   rv=x.address+x.size+x.operands[1].mem.disp-base
  around.append({"rva":hex(x.address-base),"mnemonic":x.mnemonic,"args":x.op_str,
   "target":hex(rv) if rv is not None else "","symbol":exports.get(rv,"") if rv is not None else ""})
 allout[ver]={"BEE_sha256":hashlib.sha256(blob).hexdigest(),"registration_count":len(regs),
              "entries":regs,"canonical_setup_rva":hex(site.address-base),
              "canonical_setup_neighborhood":around}
 print(ver,"REGISTRATIONS",len(regs),flush=True)
 for r in regs:print(r["index"],r["match"]["data_rva"],r["match"]["symbol"][:106],
   "CREATOR",r["creator"]["data_rva"] if r["creator"] else "MISSING_NEAR_CALL",r["creator"]["symbol"][:60] if r["creator"] else "",flush=True)
 print("CANONICAL_SETUP",ver,*[x for x in around if x["mnemonic"] in ("lea","call")],sep="\n",flush=True)
target=Path(r"D:\Developer\ShapeLayerAE\results\bee_vector_layer_62_native_tdb_creators_2025_2026.json")
target.write_text(json.dumps({"evidence":"E2-L BEE VectorLayer bootstrap typed factory and owner canonical stream registrations, static two-version PE","versions":allout},indent=2)+"\n")
print("SAVED",target)
