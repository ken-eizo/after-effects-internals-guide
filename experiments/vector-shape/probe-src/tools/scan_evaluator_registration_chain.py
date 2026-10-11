import pefile
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
for year,file,a,b in [
("2025",r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x6fdcdd,0x6fe200),
("2026",r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x720f20,0x721500)]:
 p=pefile.PE(file);raw=Path(file).read_bytes();base=p.OPTIONAL_HEADER.ImageBase
 print("==",year,hex(a),hex(b),flush=True)
 calls=[]
 for addr,size,op,ar in Cs(CS_ARCH_X86,CS_MODE_64).disasm_lite(raw[p.get_offset_from_rva(a):p.get_offset_from_rva(a)+(b-a)],base+a):
  if op in ("call","jmp"):
   calls.append((hex(addr-base),op,ar))
 for q in calls[:95]:print(*q,flush=True)
 print("total",len(calls),flush=True)
