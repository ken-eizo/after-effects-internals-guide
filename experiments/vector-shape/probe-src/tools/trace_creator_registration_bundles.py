from pathlib import Path
import pefile,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP
ROOT=Path(r"D:\Developer\After Effects Internals Guide")
all_out={}
for ver,path,ranges in [
("2025",r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",[(0x715e80,0x716882),(0x716890,0x717138),(0x717140,0x7174d0),(0x77c630,0x77d338)]),
("2026",r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",[(0x738360,0x738d4a),(0x738d50,0x7395d7),(0x7395e0,0x739958),(0x79d040,0x79dd37)])]:
    pe=pefile.PE(path);raw=Path(path).read_bytes();base=pe.OPTIONAL_HEADER.ImageBase
    imports={e.address:(m.dll.decode(errors="replace")+"!"+e.name.decode(errors="replace")) for m in pe.DIRECTORY_ENTRY_IMPORT for e in m.imports if e.name}
    md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True;out=[]
    for a,b in ranges:
        ops=[]
        for ins in md.disasm(raw[pe.get_offset_from_rva(a):pe.get_offset_from_rva(a)+(b-a)],base+a):
            if ins.mnemonic not in ("call","jmp"):continue
            target=None
            if ins.operands and ins.operands[0].type==X86_OP_MEM and ins.operands[0].mem.base==X86_REG_RIP:
                target=ins.address+ins.size+ins.operands[0].mem.disp
            elif ins.op_str.startswith("0x"):
                try:target=int(ins.op_str,16)
                except ValueError:pass
            ops.append({"rva":hex(ins.address-base),"op":ins.mnemonic+" "+ins.op_str,"import":imports.get(target,"")})
        matched=[x for x in ops if "TDB" in x["import"] or "Register" in x["import"]]
        out.append({"start":hex(a),"end":hex(b),"calls":len(ops),"imports":matched})
        print(ver,hex(a),"calls",len(ops),"TDB imports",len(matched),flush=True)
        for m in matched[:20]:print(" ",m["rva"],m["import"][:130],flush=True)
    all_out[ver]=out
dest=ROOT/"datasets"/"ae-vector-creator-registration-bundles-2025-2026.json"
dest.write_text(json.dumps({"scope":"bounded static x64 PE import callsite map, E2-L","versions":all_out},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dest)
