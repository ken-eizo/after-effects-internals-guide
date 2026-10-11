from pathlib import Path
import pefile,subprocess,re
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP,X86_OP_IMM
path=r"D:\Adobe\Adobe After Effects 2026\Support Files\TDB.dll"
p=pefile.PE(path);raw=Path(path).read_bytes();base=p.OPTIONAL_HEADER.ImageBase
iat={i.address:x.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace") for x in p.DIRECTORY_ENTRY_IMPORT for i in x.imports if i.name}
cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
for name,a,b in [("CreateStream",0x27920,0x27c60),("GetCanonicalInstance",0x27eb0,0x27f80),("GetCanonicalStream",0x27f80,0x28040),("MakeInstanceFromCanonical",0x28170,0x28220),("RegisterCanonicalInstance",0x28300,0x284e5),("UnregisterFactoryFunc",0x29c10,0x29c90)]:
 print("=== "+name,flush=True)
 for x in cs.disasm(raw[p.get_offset_from_rva(a):p.get_offset_from_rva(a)+(b-a)],base+a):
    t=None
    if x.mnemonic in ("call","jmp") and x.operands:
        o=x.operands[0]
        if o.type==X86_OP_MEM and o.mem.base==X86_REG_RIP:t=x.address+x.size+o.mem.disp
        elif o.type==X86_OP_IMM:t=o.imm
    op=iat.get(t,"")
    print(hex(x.address-base),x.mnemonic,x.op_str,("=> "+op[:115]) if op else "",flush=True)
