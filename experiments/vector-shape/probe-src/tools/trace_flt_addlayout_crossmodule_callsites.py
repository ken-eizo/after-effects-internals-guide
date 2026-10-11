"""Find REAL machine-code FF15/FF25 uses of FLT_FCSeqSpec::AddStreamToUILayout
in pinned Adobe host modules, with unwind-bounded caller context.
No host DLL loaded/called, no patching, no project changes.
"""
from pathlib import Path
import pefile,struct,json,hashlib,bisect
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
sources={
"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files"),
"2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files")}
r={}
for year,root in sources.items():
 r[year]={}
 for module in ("BEE.dll","FRP.dll"):
  path=root/module
  if not path.exists():continue
  data=path.read_bytes()
  p=pefile.PE(data=data)
  base=p.OPTIONAL_HEADER.ImageBase
  imports={i.address-base:(desc.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace"))
           for desc in p.DIRECTORY_ENTRY_IMPORT for i in desc.imports if i.name}
  targets={rva:n for rva,n in imports.items() if "AddStreamToUILayout" in n}
  syms={e.address:e.name.decode(errors="replace") for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
  bounds=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in p.DIRECTORY_ENTRY_EXCEPTION)
  starts=[v[0] for v in bounds]
  hits=[]
  for sec in p.sections:
   if not sec.Characteristics & 0x20000000:continue
   secdata=sec.get_data()
   for pattern,mn in ((b"\xff\x15","call"),(b"\xff\x25","jmp")):
    start=0
    while True:
     pos=secdata.find(pattern,start)
     if pos<0:break
     start=pos+2
     if pos+6>len(secdata):break
     site=sec.VirtualAddress+pos
     displacement=struct.unpack_from("<i",secdata,pos+2)[0]
     target=site+6+displacement
     if target not in targets:continue
     index=bisect.bisect_right(starts,site)-1
     region=bounds[index] if index>=0 and site<bounds[index][1] else None
     first,last=region or (site,site+48)
     # Disassemble bounded caller from unwind start (does not depend on
     # nearest unrelated export), and record just 8 adjacent instructions.
     ctx=[]
     if site-first<18000:
      b=data[p.get_offset_from_rva(first):p.get_offset_from_rva(min(last,site+64))]
      decoder=Cs(CS_ARCH_X86,CS_MODE_64)
      ins=list(decoder.disasm(b,base+first))
      loc=next((j for j,v in enumerate(ins) if v.address-base==site),-1)
      if loc>=0:
       ctx=[{"rva":hex(x.address-base),"m":x.mnemonic,"args":x.op_str}
            for x in ins[max(0,loc-8):loc+6]]
     record={"site":hex(site),"instruction":mn,"import_iat_rva":hex(target),
             "import":targets[target],
             "caller_pdata_start":hex(first),"caller_pdata_end":hex(last),
             "caller_export":syms.get(first,""),"context":ctx}
     hits.append(record)
  r[year][module]={"sha256":hashlib.sha256(data).hexdigest(),
                    "target_imports":[{"iat":hex(k),"name":v} for k,v in targets.items()],
                    "static_sites":hits}
  print(year,module,"target imports",len(targets),"FF15/FF25 sites",len(hits),flush=True)
  for h in hits:
   print(" ",h["site"],h["import"][:130],"fn",h["caller_pdata_start"],h["caller_export"][:110],flush=True)
out=Path(r"D:\Developer\ShapeLayerAE\results\flt_addstream_to_uilayout_crossmodule_direct_sites_2025_2026.json")
out.write_text(json.dumps({"classification":"E2-L exact on-disk executable FF15/FF25 relocations; indirect dispatch not exhaustive","years":r},indent=2)+"\n")
print("SAVED",out,flush=True)
