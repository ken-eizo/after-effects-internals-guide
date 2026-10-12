"""Compare true layer-owning BEE_VectorLayer constructor call in
BEE_Layer::CreateLayerFromType with TDB_StreamBase creator callback.
Read-only native code for two pinned AE installs.
"""
from pathlib import Path
import pefile,json,bisect
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM
paths={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll","2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
report={}
for y,path in paths.items():
 p=pefile.PE(path);raw=Path(path).read_bytes();base=p.OPTIONAL_HEADER.ImageBase
 exports={e.address:e.name.decode(errors="replace") for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 rva=next(k for k,v in exports.items() if v.startswith("?CreateLayerFromType@BEE_Layer@@"))
 pdata=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION)
 k=bisect.bisect_right([a for a,b in pdata],rva)-1;a,b=pdata[k]
 decoder=Cs(CS_ARCH_X86,CS_MODE_64);decoder.detail=True
 ins=list(decoder.disasm(raw[p.get_offset_from_rva(a):p.get_offset_from_rva(b)],base+a))
 matches=[]
 for i,x in enumerate(ins):
  if x.mnemonic!="call" or not x.operands or x.operands[0].type!=X86_OP_IMM:continue
  target=x.operands[0].imm-base
  symbol=exports.get(target,"")
  if not symbol.startswith("??0BEE_VectorLayer@@"):continue
  before=[{"rva":hex(v.address-base),"op":v.mnemonic,"args":v.op_str} for v in ins[max(0,i-22):i+2]]
  matches.append({"ctor_rva":hex(target),"callsite":hex(x.address-base),"instructions":before})
 assert len(matches)==1,(y,matches)
 report[y]={"native_vector_ctor_call":matches[0],
            "stock_type_switch_controls_constructor":True}
 print(y,"VECTORCTOR",matches[0]["ctor_rva"],"CALL",matches[0]["callsite"],flush=True)
 for v in matches[0]["instructions"]:print("  ",v["rva"],v["op"],v["args"],flush=True)
out=Path(r"D:\Developer\ShapeLayerAE\results\bee_native_vector_owner_constructor_stock_dispatch_context_2025_2026.json")
out.write_text(json.dumps({"evidence":"E2-L BEE stock layer-constructor dispatch with actual BEE_CompItem parent arguments, no runtime calls","versions":report},indent=2)+"\n")
print("SAVED",out)
