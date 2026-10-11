"""Print bounded EndEffect instructions surrounding virtual CreateEffectGroup and
canonical instance registration. Static only.
"""
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
v={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x2f6bc0,0x2f6c60),
   "2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x2ff7d0,0x2ff880)}
for year,(path,a,b) in v.items():
 p=pefile.PE(path);base=p.OPTIONAL_HEADER.ImageBase
 s=p.__data__[p.get_offset_from_rva(a):p.get_offset_from_rva(b)]
 print("\n====",year,flush=True)
 for x in Cs(CS_ARCH_X86,CS_MODE_64).disasm(s,base+a):
  print(f"{x.address-base:08x} {x.mnemonic:<9} {x.op_str}",flush=True)
