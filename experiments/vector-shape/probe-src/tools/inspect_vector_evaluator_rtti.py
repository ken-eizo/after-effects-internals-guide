from pathlib import Path
import pefile,struct
p=pefile.PE(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")
m=p.get_memory_mapped_image();base=p.OPTIONAL_HEADER.ImageBase
for loc in [0x1061c00,0x1061be0,0x1061c30]:
 try:
  col_va=struct.unpack_from("<Q",m,loc-8)[0]
  col_rva=col_va-base
  typ=struct.unpack_from("<i",m,col_rva+12)[0] if col_rva>=0 else -1
  name=m[typ+16:typ+128].split(bytes([0]))[0].decode(errors="replace") if typ>=0 else ""
  print(hex(loc),"COL",hex(col_rva),"TDRVA",hex(typ),"RTTI",name)
 except Exception as e:print(hex(loc),str(e)[:100])
