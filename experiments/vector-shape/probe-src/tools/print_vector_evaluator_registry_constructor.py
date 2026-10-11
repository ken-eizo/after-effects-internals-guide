import pefile,bisect
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
p=pefile.PE(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")
data=Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll").read_bytes()
fs=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in p.DIRECTORY_ENTRY_EXCEPTION)
starts=[x[0] for x in fs]
cs=Cs(CS_ARCH_X86,CS_MODE_64)
for label,point in [("construct",0x713550),("post_init",0x713670),("helper",0x711fa0),("destruct",0x7217c0),("filter",0x6f1590)]:
 i=bisect.bisect_right(starts,point)-1
 if not(i>=0 and point<fs[i][1]):continue
 a,b=fs[i]
 print("==",label,hex(a),hex(b),"bytes",b-a,flush=True)
 for addr,size,op,args in cs.disasm_lite(data[p.get_offset_from_rva(a):p.get_offset_from_rva(a)+(b-a)],p.OPTIONAL_HEADER.ImageBase+a):
  if b-a<1200 or op.startswith("call") or addr-p.OPTIONAL_HEADER.ImageBase<a+280:
   print(hex(addr-p.OPTIONAL_HEADER.ImageBase),op,args,flush=True)
