"""Find direct x86-64 E8 callsites (and E9 jumps) to the internal
LayerStyle XML dynamic parser initializer, classify unwind caller.
Only installed BEE PE images are read. Candidate byte matches revalidated.
"""
from pathlib import Path
import pefile,struct,bisect,json,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
cfg={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x2fbb60),
     "2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x304640)}
out={}
for year,(file,target) in cfg.items():
 b=Path(file).read_bytes();p=pefile.PE(data=b);base=p.OPTIONAL_HEADER.ImageBase
 bounds=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION)
 starts=[x[0] for x in bounds]
 syms={e.address:e.name.decode(errors="replace") for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 hits=[]
 for sec in p.sections:
  if not sec.Characteristics & 0x20000000:continue
  data=sec.get_data()
  for opcode in (0xe8,0xe9):
   pos=0
   while True:
    site=data.find(bytes([opcode]),pos)
    if site<0 or site+5>len(data):break
    pos=site+1
    rva=sec.VirtualAddress+site
    callee=rva+5+struct.unpack_from("<i",data,site+1)[0]
    if callee!=target:continue
    i=bisect.bisect_right(starts,rva)-1
    span=bounds[i] if i>=0 and rva<bounds[i][1] else None
    hits.append({"site_rva":hex(rva),"kind":"CALL" if opcode==0xe8 else "JMP",
       "caller_pdata_rva":[hex(s) for s in span] if span else None,
       "caller_export":syms.get(span[0],"") if span else "",
       "byte_context":data[max(0,site-20):site+25].hex()})
 print(year,"direct candidate xrefs",len(hits),flush=True)
 for h in hits:print(h,flush=True)
 out[year]={"sha256":hashlib.sha256(b).hexdigest(),"target":hex(target),
            "direct_relative_sites":hits}
dst=Path(r"D:\Developer\ShapeLayerAE\results\bee_layerstyle_xml_parser_entry_xrefs_2025_2026.json")
dst.write_text(json.dumps({"classification":"E2-L candidate x64 call/jmp sites; indirect calls not covered","versions":out},indent=2)+"\n")
print("SAVED",dst)
