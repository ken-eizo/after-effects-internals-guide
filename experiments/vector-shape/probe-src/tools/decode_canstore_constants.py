"""Resolve RIP-relative references from BEE VectorStreamGroup::CanStore and decode local constants offline."""
import pefile,json
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP
data=json.load(open(r"D:\Developer\After Effects Internals Guide\datasets\ae-tdb-vector-canstore-disasm-2025-2026.json"))
for ver,basepath in [("2025",r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),("2026",r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")]:
    p=pefile.PE(basepath)
    blob=Path(basepath).read_bytes()
    b=p.OPTIONAL_HEADER.ImageBase
    arr=data["versions"][ver]["BEE.dll"]
    x=[r for r in arr if "CanStore@VectorsStreamGroup" in r["name"]][0]
    rv=int(x["rva"],16)
    decoder=Cs(CS_ARCH_X86,CS_MODE_64);decoder.detail=True
    print("====",ver)
    for instr in decoder.disasm(blob[p.get_offset_from_rva(rv):p.get_offset_from_rva(rv)+320],b+rv):
        if instr.mnemonic not in ("lea","mov") or not instr.operands:continue
        for o in instr.operands:
            if o.type!=X86_OP_MEM or o.mem.base!=X86_REG_RIP:continue
            addr=instr.address+instr.size+o.mem.disp
            rr=addr-b
            if rr<0:continue
            try:by=blob[p.get_offset_from_rva(rr):p.get_offset_from_rva(rr)+90]
            except Exception:continue
            asc=by.split(b"\x00")[0][:55]
            dec=asc.decode("latin1","replace")
            utf=by.decode("utf-16-le","replace").split("\x00")[0][:30]
            print(hex(instr.address-b),instr.mnemonic,instr.op_str,"->",hex(rr),"ASCII",ascii(dec),"UTF16",ascii(utf))
