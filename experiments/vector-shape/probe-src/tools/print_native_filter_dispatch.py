from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
f=r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"
p=pefile.PE(f);b=Path(f).read_bytes()
a=0x6f1590;z=0x6f1675
print("AE2026 BEE VectorArt::StreamBasedFilter::DoFilter")
for addr,size,op,args in Cs(CS_ARCH_X86,CS_MODE_64).disasm_lite(b[p.get_offset_from_rva(a):p.get_offset_from_rva(a)+(z-a)],p.OPTIONAL_HEADER.ImageBase+a):
 print(f"{addr-p.OPTIONAL_HEADER.ImageBase:08x} {op:<7} {args}")
