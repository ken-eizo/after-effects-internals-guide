"""Static inspect unknown vector evaluator lookup, both installed versions."""
import pefile
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
cfg=[("2025",r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",[(0x6f87e0,0x6f8826),(0x6f9020,0x6f90ed)]),
("2026",r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",[(0x71c2f0,0x71c336),(0x71cc00,0x71ccc9)])]
for year,path,functions in cfg:
 p=pefile.PE(path);raw=Path(path).read_bytes();base=p.OPTIONAL_HEADER.ImageBase
 print("=== ",year,flush=True)
 for a,b in functions:
  print("RVA",hex(a),"len",b-a,flush=True)
  for x in Cs(CS_ARCH_X86,CS_MODE_64).disasm(raw[p.get_offset_from_rva(a):p.get_offset_from_rva(a)+(b-a)],base+a):
   print(hex(x.address-base),x.mnemonic,x.op_str,flush=True)
