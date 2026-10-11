from capstone import Cs,CS_ARCH_X86,CS_MODE_64
import pefile
for title,path,rva in [("AE2025",r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x36ddf0),("AE2026",r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x378810)]:
    p=pefile.PE(path);base=p.OPTIONAL_HEADER.ImageBase
    with open(path,"rb") as f:
        f.seek(p.get_offset_from_rva(rva));data=f.read(350)
    md=Cs(CS_ARCH_X86,CS_MODE_64)
    print("==",title,hex(rva))
    for ins in md.disasm(data,base+rva):
        print(hex(ins.address-base), ins.mnemonic,ins.op_str)
        if ins.address-base>rva+290:break
