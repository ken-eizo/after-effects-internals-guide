import pefile,bisect
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
for ver,file,point in [("2025",r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x6fdcc0),("2026",r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x713120)]:
 p=pefile.PE(file)
 starts=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION)
 idx=bisect.bisect_right([a for a,b in starts],point)-1
 a,b=starts[idx]
 print("==",ver,hex(a),hex(b),"bytes",b-a,flush=True)
 raw=Path(file).read_bytes()
 for addr,size,op,arg in Cs(CS_ARCH_X86,CS_MODE_64).disasm_lite(raw[p.get_offset_from_rva(a):p.get_offset_from_rva(a)+(b-a)],p.OPTIONAL_HEADER.ImageBase+a):
  if ver=="2026" or op in ("call","jmp","lea"):
   print(hex(addr-p.OPTIONAL_HEADER.ImageBase),op,arg,flush=True)
