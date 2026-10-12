"""Decode all 11 LayerStyle parser temporary TDB registered identities,
plus XML parse source via native RIP-relative operand path. Read-only.
"""
import pefile,struct,json,hashlib
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP
bins={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x2fbb60,0x2fc0c0),
      "2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x304640,0x304bad)}
out={}
for year,(file,start,end) in bins.items():
 blob=Path(file).read_bytes();pe=pefile.PE(data=blob);base=pe.OPTIONAL_HEADER.ImageBase
 ents={e.name.decode(errors="replace"):e.address for e in pe.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 from capstone import Cs
 dis=Cs(CS_ARCH_X86,CS_MODE_64);dis.detail=True
 ins=list(dis.disasm(blob[pe.get_offset_from_rva(start):pe.get_offset_from_rva(end)],base+start))
 imports={i.address:desc.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace") for desc in pe.DIRECTORY_ENTRY_IMPORT for i in desc.imports if i.name}
 registrations=[]
 for i,x in enumerate(ins):
  if x.mnemonic!="call" or not x.operands:continue
  arg=x.operands[0]
  if arg.type!=X86_OP_MEM or arg.mem.base!=X86_REG_RIP:continue
  iat=x.address+x.size+arg.mem.disp
  sym=imports.get(iat,"")
  if "?Register@TDB_ScRegisterStreams@@" not in sym:continue
  pre=ins[max(0,i-11):i]
  entries=[]
  for v in pre:
   if v.mnemonic!="lea" or not v.operands:continue
   m=v.operands[-1]
   if m.type==X86_OP_MEM and m.mem.base==X86_REG_RIP:
    rr=v.address+v.size+m.mem.disp-base
    raw=b""
    try:raw=blob[pe.get_offset_from_rva(rr):pe.get_offset_from_rva(rr)+48]
    except Exception:pass
    symbol=next((n for n,rva in ents.items() if rva==rr),"")
    entries.append({"site":hex(v.address-base),"dest":v.op_str.split(",")[0],
                    "target_rva":hex(rr),"export":symbol,"hex48":raw.hex()})
  registrations.append({"callsite":hex(x.address-base),"rip_sources":entries})
 print(year,"registered",len(registrations))
 assert len(registrations)==11
 for n,r in enumerate(registrations):
  print(n,r["callsite"],"symbols",[(i["dest"],i["target_rva"],i["export"][:95]) for i in r["rip_sources"]],flush=True)
 out[year]={"sha256":hashlib.sha256(blob).hexdigest(),"registration_calls":registrations}
dst=Path(r"D:\Developer\ShapeLayerAE\results\layer_style_scoped_registered_type_sources_2025_2026.json")
dst.write_text(json.dumps({"evidence":"E2-L native caller RIP operand source map, no host API use","versions":out},indent=2)+"\n")
print("SAVED",dst)
