from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
p=pefile.PE(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")
raw=Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll").read_bytes()
start=0x7217c0;end=0x721d8c
print("BEE26 - evaluator setup",hex(start),hex(end),end-start)
for i,(addr,size,op,args) in enumerate(Cs(CS_ARCH_X86,CS_MODE_64).disasm_lite(raw[p.get_offset_from_rva(start):p.get_offset_from_rva(start)+(end-start)],p.OPTIONAL_HEADER.ImageBase+start)):
 if i<135 or op in ("call","jmp","lea"):
  print(f"{addr-p.OPTIONAL_HEADER.ImageBase:08x} {op:<7} {args}")
