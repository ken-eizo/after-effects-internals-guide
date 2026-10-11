from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
path=r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"
pe=pefile.PE(path);raw=Path(path).read_bytes()
for title,start,end in [("VisitArtStream",0x710790,0x7109ea),("DispatchSingleVectorStream",0x711040,0x71114d)]:
 print("###",title)
 for i in Cs(CS_ARCH_X86,CS_MODE_64).disasm(raw[pe.get_offset_from_rva(start):pe.get_offset_from_rva(end)],pe.OPTIONAL_HEADER.ImageBase+start):
  print(f"{i.address-pe.OPTIONAL_HEADER.ImageBase:08x} {i.mnemonic:<7} {i.op_str}")
