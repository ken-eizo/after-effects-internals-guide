from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
p=pefile.PE(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")
data=Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll").read_bytes()
for a,b in [(0x1a83c,0x1a8d0),(0x1b620,0x1b69c)]:
 print("==",hex(a))
 for addr,size,op,arg in Cs(CS_ARCH_X86,CS_MODE_64).disasm_lite(data[p.get_offset_from_rva(a):p.get_offset_from_rva(a)+(b-a)],p.OPTIONAL_HEADER.ImageBase+a):
  print(hex(addr-p.OPTIONAL_HEADER.ImageBase),op,arg)
