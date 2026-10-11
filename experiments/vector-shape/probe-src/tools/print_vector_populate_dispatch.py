"""Print concise disassembly of native PopulateVectorArt for inspection."""
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
locs=[("2025",r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x6ecb60,260),
("2026",r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x710ee0,171)]
for ver,path,rva,size in locs:
 p=pefile.PE(path);b=Path(path).read_bytes()
 print("###",ver,flush=True)
 for i in Cs(CS_ARCH_X86,CS_MODE_64).disasm(b[p.get_offset_from_rva(rva):p.get_offset_from_rva(rva)+size],p.OPTIONAL_HEADER.ImageBase+rva):
  print(f"{i.address-p.OPTIONAL_HEADER.ImageBase:08x} {i.mnemonic:<8} {i.op_str}",flush=True)
