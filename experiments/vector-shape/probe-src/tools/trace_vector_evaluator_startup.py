from pathlib import Path
import pefile,bisect
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
loc=[("2025",r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x76b6fb),
("2026",r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x78cf6b)]
for ver,pth,addr in loc:
 p=pefile.PE(pth);raw=Path(pth).read_bytes();base=p.OPTIONAL_HEADER.ImageBase
 bounds=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in p.DIRECTORY_ENTRY_EXCEPTION)
 starts=[x[0] for x in bounds]
 i=bisect.bisect_right(starts,addr)-1
 a,b=bounds[i]
 print("==",ver,"startup callee",hex(a),hex(b),"size",b-a)
 cs=Cs(CS_ARCH_X86,CS_MODE_64)
 for j,(adr,size,op,args) in enumerate(cs.disasm_lite(raw[p.get_offset_from_rva(a):p.get_offset_from_rva(a)+(b-a)],base+a)):
  if j<90 or op=="call":
   print(hex(adr-base),op,args)
