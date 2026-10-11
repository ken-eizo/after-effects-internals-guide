"""Recover native VectorStreamGroup CanStore string literals at RIP-relative addresses.
Static binary evidence only. Never execute Adobe code.
"""
from pathlib import Path
from hashlib import sha256
import json,pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP
binaries={
"2025":(Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),0x700250),
"2026":(Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"),0x723C80)
}
out={}
for ver,(path,rva) in binaries.items():
    raw=path.read_bytes();p=pefile.PE(data=raw);base=p.OPTIONAL_HEADER.ImageBase
    md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
    matches=[]
    off=p.get_offset_from_rva(rva)
    for inst in md.disasm(raw[off:off+240],base+rva):
        if inst.mnemonic!="lea":continue
        for arg in inst.operands:
            if arg.type!=X86_OP_MEM or arg.mem.base!=X86_REG_RIP:continue
            ptr=inst.address+inst.size+arg.mem.disp;ref_rva=ptr-base
            try:string_raw=raw[p.get_offset_from_rva(ref_rva):p.get_offset_from_rva(ref_rva)+64]
            except Exception:continue
            literal=string_raw.split(b"\x00")[0]
            if not literal.startswith(b"ADBE Vector "):continue
            text=literal.decode("ascii","replace")
            matches.append({"instruction_rva":hex(inst.address-base),"literal_rva":hex(ref_rva),"literal":text})
    out[ver]={"BEE_sha256":sha256(raw).hexdigest(),"predicate_rva":hex(rva),"strings":matches}
dest=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-vector-canstore-prefix-literals-2025-2026.json")
dest.write_text(json.dumps({"evidence":"E2-L local binary literal references, no native predicate invocation","versions":out},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
for version,v in out.items():print(version,v["strings"])
print("ARCHIVED",dest)
