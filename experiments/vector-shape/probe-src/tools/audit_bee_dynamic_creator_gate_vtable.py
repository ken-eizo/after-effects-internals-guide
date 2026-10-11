"""Resolve true BEE DynamicStreamEffectsParser vtable methods for EndEffect:
+0x98 (gate), +0xa0 (hidden), +0xb0 (group creator).
Only static pointers from two pinned host DLLs; no host calls.
"""
from pathlib import Path
import pefile,struct,json,hashlib
r={}
for year,file in (("2025",r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
                  ("2026",r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")):
 data=Path(file).read_bytes();p=pefile.PE(data=data);base=p.OPTIONAL_HEADER.ImageBase
 syms={s.name.decode(errors="replace"):s.address for s in p.DIRECTORY_ENTRY_EXPORT.symbols if s.name}
 v=next((s for s in syms if s.startswith("??_7DynamicStreamEffectsParser@BEE@ae@@6B@")))
 off=syms[v]
 slots={}
 for index in (0x88//8,0x98//8,0xa0//8,0xb0//8):
  ptr=struct.unpack_from("<Q",data,p.get_offset_from_rva(off)+index*8)[0]
  target=ptr-base
  name=next((n for n,a in syms.items() if a==target),"")
  slots[hex(index*8)]={"index":index,"rva":hex(target),"export":name}
  print(year,hex(index*8),hex(target),name[:180],flush=True)
 assert "CreateEffectGroup@DynamicStreamEffectsParser" in slots["0xb0"]["export"]
 r[year]={"sha256":hashlib.sha256(data).hexdigest(),"vtable_rva":hex(off),"sites":slots}
dst=Path(r"D:\Developer\ShapeLayerAE\results\bee_dynamic_effect_creator_gate_vtable_2025_2026.json")
dst.write_text(json.dumps({"evidence":"static MSVC class vtable, PE-discovered exports only","versions":r},indent=2)+"\n")
print("SAVED",dst)
