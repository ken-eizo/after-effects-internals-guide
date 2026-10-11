"""Native Dynamic Effects Parser vtable creation hook audit.
Only on-disk BEE.dll, no code loaded, no Adobe host operation.
"""
import struct,json,hashlib
from pathlib import Path
import pefile
files={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
       "2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")}
out={}
for year,path in files.items():
 b=path.read_bytes();pe=pefile.PE(data=b);base=pe.OPTIONAL_HEADER.ImageBase
 names={e.name.decode(errors="replace"):e.address for e in pe.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 vtable=[(n,a) for n,a in names.items() if n.startswith("??_7") and "EffectsParser@" in n]
 creators=[(n,a) for n,a in names.items() if n.startswith("?CreateEffectGroup@") and "EffectsParser@" in n]
 assert len(creators)>=1,(year,creators)
 key,val=next((n,a) for n,a in creators if "DynamicStreamEffectsParser@BEE@ae" in n)
 exactvt=next((n,a) for n,a in vtable if n.startswith("??_7DynamicStreamEffectsParser@BEE@ae@@6B@"))
 def rva_list(at,count):
  raw=b[pe.get_offset_from_rva(at):][:8*count]
  return struct.unpack_from("<"+str(count)+"Q",raw,0)
 vtname,vtrva=exactvt
 slots=rva_list(vtrva,110)
 positions=[i for i,p in enumerate(slots) if p==base+val]
 assert len(positions)==1,(year,positions)
 pos=positions[0]
 peers=[]
 for n,adr in vtable:
  if "DynamicStreamEffectsParser@" not in n:
   # Different-class (EffectsParser) vtables need not have the same
   # number or layout of slots; never interpret raw neighbor data.
   peers.append({"vtable":n,"rva":hex(adr),
                 "note":"non-comparable base/sibling vtable, slot omitted"})
   continue
  ptr=rva_list(adr,pos+1)[pos]
  rr=ptr-base
  name=next((name for name,a in names.items() if a==rr),"")
  peers.append({"vtable":n,"rva":hex(adr),"factory_slot":pos,
                 "handler_rva":hex(rr),"handler_symbol":name,
                 "same_base_null_creator":rr==val})
 out[year]={"sha256":hashlib.sha256(b).hexdigest(),"vtable":vtname,
            "factory_slot_index":pos,
            "base_creator_rva":hex(val),
            "related_parser_vtables":peers,
            "warning":"vtable survey limited to exported EffectsParser vtables, not every hidden derived type"}
 print("YEAR",year,"CREATE GROUP SLOT",pos,"base",hex(val),"related vtables",len(peers),flush=True)
 for item in peers:
  print(item["vtable"][:105],"handler",item.get("handler_rva","not-comparable"),
        "same",item.get("same_base_null_creator","N/A"),flush=True)
dst=Path(r"D:\Developer\ShapeLayerAE\results\dynamic_effect_parser_group_creator_vtable_2025_2026.json")
dst.write_text(json.dumps({"evidence":"static exported MSVC parser vtables, no private calls","versions":out},indent=2)+"\n",encoding="utf-8")
print("SAVED",dst)
