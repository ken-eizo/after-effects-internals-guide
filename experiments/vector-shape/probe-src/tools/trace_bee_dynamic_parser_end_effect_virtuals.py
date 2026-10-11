"""Inspect native DynamicStreamEffectsParser::EndEffect virtual calls
relative to CreateEffectGroup slot 0xb0 (index22), pinned AE2025/26.
Static disassembly only; no executable modules loaded.
"""
from pathlib import Path
import pefile,json,hashlib,bisect
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
years={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x2f6800),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x2ff440)}
out={}
for year,(file,start) in years.items():
 b=Path(file).read_bytes();p=pefile.PE(data=b);base=p.OPTIONAL_HEADER.ImageBase
 funcs=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION)
 ix=bisect.bisect_right([x[0] for x in funcs],start)-1
 assert ix>=0 and start<funcs[ix][1]
 end=funcs[ix][1]
 exports={s.address:s.name.decode(errors="replace") for s in p.DIRECTORY_ENTRY_EXPORT.symbols if s.name}
 imports={i.address-base:(des.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace"))
          for des in p.DIRECTORY_ENTRY_IMPORT for i in des.imports if i.name}
 cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
 ins=[];calls=[];vtable=[]
 for x in cs.disasm(b[p.get_offset_from_rva(start):p.get_offset_from_rva(end)],base+start):
  row={"rva":hex(x.address-base),"m":x.mnemonic,"args":x.op_str}
  ins.append(row)
  if x.mnemonic in ("call","jmp"):
   calls.append(row)
   if "+ 0xb0" in x.op_str or "+ 0x88" in x.op_str or "+ 0x80" in x.op_str:
    vtable.append(row)
  if x.mnemonic=="call" and "rip +" in x.op_str:
   from capstone.x86_const import X86_OP_MEM,X86_REG_RIP
   if x.operands[0].type==X86_OP_MEM and x.operands[0].mem.base==X86_REG_RIP:
    iat=x.address+x.size+x.operands[0].mem.disp-base
    row["resolved_import"]=imports.get(iat,"")
  if x.mnemonic in ("call","jmp") and x.op_str.startswith("0x"):
   t=int(x.op_str,16)-base
   row["resolved_export"]=exports.get(t,"")
 out[year]={"BEE_sha256":hashlib.sha256(b).hexdigest(),"EndEffect_rva":hex(start),
            "pdata_end":hex(end),"calls":calls,"virtual_calls_0xb0_0x88_0x80":vtable}
 print(year,"EndEffect size",hex(end-start),"total calls/jumps",len(calls))
 for r in vtable:print("VIRTUAL",r,flush=True)
 for r in calls:
  target=r.get("resolved_export") or r.get("resolved_import","")
  if any(k in target for k in ("AddStreamToUILayout","StreamFactory","TDB_Stream","FLT_FCSeq","SetupCanonical")):
   print("EDGE",r["rva"],target[:180],flush=True)
p=Path(r"D:\Developer\ShapeLayerAE\results\bee_dynamic_parser_end_effect_vtable_dispatch_2025_2026.json")
p.write_text(json.dumps({"scope":"unwind-bounded native EndEffect direct and virtual call disassembly; no host invocation","years":out},indent=2)+"\n")
print("SAVED",p)
