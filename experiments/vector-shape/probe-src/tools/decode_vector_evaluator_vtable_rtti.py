"""Recover MSVC RTTI for BEE evaluator objects instantiated near 20 registry calls.
Static local PE RTTI metadata only; multiple inheritance may expose >1 vftable.
"""
from pathlib import Path
import pefile,struct,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP
root=Path(r"D:\Developer\After Effects Internals Guide")
regs=json.loads((root/"datasets/ae-native-vector-evaluator-registration-records-2025-2026.json").read_text())["versions"]
cfg={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x6fd400),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x720f20)}
results={}
for year,(path,start) in cfg.items():
 p=pefile.PE(path);raw=Path(path).read_bytes();base=p.OPTIONAL_HEADER.ImageBase
 md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
 image=p.get_memory_mapped_image()
 rows=[]
 prev=start
 for row in regs[year]["records"]:
  call=int(row["registrar_call_rva"],16)
  seq=list(md.disasm(raw[p.get_offset_from_rva(prev):p.get_offset_from_rva(prev)+(call-prev)],base+prev))
  found=[]
  for ins in seq:
   if ins.mnemonic!="lea" or len(ins.operands)!=2:continue
   m=ins.operands[1]
   if m.type!=X86_OP_MEM or m.mem.base!=X86_REG_RIP:continue
   rva=ins.address+ins.size+m.mem.disp-base
   if rva<16 or rva+24>len(image):continue
   try:
    col=struct.unpack_from("<Q",image,rva-8)[0]-base
    if not (0<=col+24<len(image)):continue
    sig,offset,cd,rtti=struct.unpack_from("<IIII",image,col)
    if sig!=1:continue
    typ=struct.unpack_from("<i",image,col+12)[0]
    if not (0<=typ+30<len(image)):continue
    s=image[typ+16:typ+230].split(b"\0")[0].decode("ascii","replace")
    if s.startswith(".?AV") or s.startswith(".?AU"):
     found.append({"reference_instruction_rva":hex(ins.address-base),"vtable_rva":hex(rva),"class_rtti":s,"secondary_vtable_offset":offset})
   except Exception:pass
  rows.append({"registration_call_rva":hex(call),"matched_evaluator_classes":found})
  prev=call+5
 results[year]={"records":rows}
 print("==",year,flush=True)
 for j,x in enumerate(rows):
  print(j+1,x["registration_call_rva"],[(c["class_rtti"],c["secondary_vtable_offset"]) for c in x["matched_evaluator_classes"][-6:]],flush=True)
out=root/"datasets"/"ae-native-vector-evaluator-vtable-rtti-2025-2026.json"
out.write_text(json.dumps({"classification":"E2-L static RTTI from callsite-local vtable pointers; not full ABI","versions":results},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",out)
