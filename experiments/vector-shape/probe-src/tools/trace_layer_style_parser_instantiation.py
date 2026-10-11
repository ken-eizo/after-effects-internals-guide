"""Find native constructors writing the derived LayerStyleStreamGroupParser
vftable via RIP-relative LEA. On-disk AE2025/26 BEE .text only.
"""
from pathlib import Path
import pefile,struct,bisect,json,hashlib
v={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0xf4cbb8),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0xfa9f98)}
out={}
for year,(file,target) in v.items():
 data=Path(file).read_bytes();p=pefile.PE(data=data)
 ex={e.address:e.name.decode(errors="replace") for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 fs=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in p.DIRECTORY_ENTRY_EXCEPTION)
 begins=[x[0] for x in fs];hits=[]
 for section in p.sections:
  if not section.Characteristics & 0x20000000:continue
  b=section.get_data();i=0
  while i<len(b)-7:
   pos=b.find(b"\x8d",i)
   if pos<0 or pos+6>=len(b):break
   i=pos+1
   if pos==0:continue
   rex=b[pos-1]
   if rex not in (0x48,0x49,0x4c,0x4d):continue
   modrm=b[pos+1]
   if (modrm & 0xc7)!=0x05:continue
   site=section.VirtualAddress+pos-1
   disp=struct.unpack_from("<i",b,pos+2)[0]
   resolved=site+7+disp
   if resolved!=target:continue
   ix=bisect.bisect_right(begins,site)-1
   own=fs[ix] if ix>=0 and site<fs[ix][1] else None
   hits.append({"code_rva":hex(site),"opcodes":b[pos-1:pos+6].hex(),
      "rtti_derived_vtable_rva":hex(target),
      "caller_pdata":[hex(x) for x in own] if own else None,
      "caller_exact_export":ex.get(own[0],"") if own else ""})
 print("YEAR",year,"xref hits",len(hits),flush=True)
 for x in hits:print(x,flush=True)
 out[year]={"sha256":hashlib.sha256(data).hexdigest(),
            "derived_parser_vtable_rva":hex(target),
            "executable_rip_relative_LEA_refs":hits}
dst=Path(r"D:\Developer\ShapeLayerAE\results\bee_layer_style_parser_constructor_sites_2025_2026.json")
dst.write_text(json.dumps({"evidence":"E2-L candidate LEA RIP xrefs, no runtime code","versions":out},indent=2)+"\n")
print("SAVED",dst)
