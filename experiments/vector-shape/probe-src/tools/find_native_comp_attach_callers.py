"""Find BEE native direct rel32 callsites into CompItem attach functions,
stock layer factory, and Shape layer creator. Tie to exported names and
.pdata function bounds on installed AE2025/2026. Static-only.
"""
from pathlib import Path
import pefile,bisect,json,struct
names=[
"?AttachLayerToCompAndLayerParamsOnly@BEE_CompItem@@",
"?AttachLayerToCompOnly@BEE_CompItem@@",
"?CreateLayerFromType@BEE_Layer@@",
"?BEE_CmdNewVectorLayer@@"
]
paths={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
"2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
out={}
for year,path in paths.items():
 p=pefile.PE(path);raw=Path(path).read_bytes()
 symbols={e.name.decode(errors="replace"):e.address for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 exact_export_by_rva={v:k for k,v in symbols.items()}
 targets={}
 for pattern in names:
  m=[(k,v) for k,v in symbols.items() if k.startswith(pattern)]
  assert len(m)==1,(year,pattern)
  targets[m[0][0]]=m[0][1]
 pdata=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in p.DIRECTORY_ENTRY_EXCEPTION)
 starts=[a for a,b in pdata]
 owner={}
 for sect in p.sections:
  if not (sect.Characteristics&0x20000000):continue
  data=sect.get_data();at=0
  while True:
   at=data.find(b"\xe8",at)
   if at<0:break
   if at+5<len(data):
    src=sect.VirtualAddress+at
    dst=src+5+struct.unpack_from("<i",data,at+1)[0]
    if dst in targets.values():
     idx=bisect.bisect_right(starts,src)-1
     a,b=pdata[idx] if idx>=0 else (None,None)
     if a is not None and src<b:
      owner.setdefault(dst,[]).append({"caller_rva":hex(src),
      "within_pdata":hex(a),"is_function_entry_exported":a in exact_export_by_rva,
      "parent_export":exact_export_by_rva.get(a,"")})
   at+=1
 entries={}
 for name,addr in targets.items():
  sources=owner.get(addr,[])
  entries[name]={"target_rva":hex(addr),"raw_direct_calls_inside_bounded_functions":sources}
  print(year,name,"CALLED_BY",len(sources),flush=True)
  for x in sources[:30]:print(" ",x,flush=True)
 out[year]=entries
dest=Path(r"D:\Developer\ShapeLayerAE\results\bee_comp_attach_native_callers_2025_2026.json")
dest.write_text(json.dumps({"scope":"E2-L static raw CALL bytes inside BEE.dll pdata; unverified instruction boundary; not a complete dynamic call graph","versions":out},indent=2)+"\n")
print("SAVED",dest)
