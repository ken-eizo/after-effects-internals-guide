"""EXP-SHAPE-025: are Shape layers created through a generic layer-kind command?
Dump exact native code for BEE_CmdNewVectorLayer and BEE_CmdNewLayer,
ModelItem::CreateNewLayer, and type constructors in AE2025 and AE2026.
No running AE interaction.
"""
from pathlib import Path
import subprocess,pefile,re,json,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_OP_IMM,X86_REG_RIP
root=Path(r"D:\Developer\After Effects Internals Guide")
binary={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
"2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")}
symbols_of_interest=[
"?BEE_CmdNewVectorLayer@@",
"?BEE_CmdNewLayer@@",
"?GetLayerType@BEE_VectorLayer@@",
"?GetLayerType@BEE_AVLayer@@",
"?GetDefaultTypeMagic@BEE_VectorLayer@@",
"?CreateNewLayer@BEE_ModelItem@@",
"?Create@BEE_VectorLayer@@",
"?Create@BEE_AVLayer@@"
]
pat=re.compile(r"^\s*\d+\s+[0-9a-fA-F]+\s+([0-9a-fA-F]{8})\s+(\S+)")
report={}
for ver,path in binary.items():
 raw=path.read_bytes();p=pefile.PE(data=raw);base=p.OPTIONAL_HEADER.ImageBase
 export={}
 for ln in subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,errors="replace",check=True).stdout.splitlines():
  m=pat.match(ln)
  if m:export[int(m.group(1),16)]=m.group(2)
 imports={i.address:t.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace")
   for t in p.DIRECTORY_ENTRY_IMPORT for i in t.imports if i.name}
 cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
 funcs=[]
 for q in symbols_of_interest:
  for address,name in export.items():
   if q not in name:continue
   # 0x100 bytes enough to show tiny command adapters and return constants.
   stream=raw[p.get_offset_from_rva(address):p.get_offset_from_rva(address)+0x120]
   codes=[]
   for n,i in enumerate(cs.disasm(stream,base+address)):
    if n>65:break
    annotations=[]
    if i.mnemonic in ("call","jmp") and i.operands:
     op=i.operands[0];target=None
     if op.type==X86_OP_IMM:target=op.imm
     elif op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
      target=i.address+i.size+op.mem.disp
     if target is not None:
      annotations.append(export.get(target-base) or imports.get(target) or "target RVA "+hex(target-base))
    codes.append({"rva":hex(i.address-base),"mnemonic":i.mnemonic,"operands":i.op_str,
                  "resolved_calls":annotations})
    if i.mnemonic in ("ret","int3") and n>1:break
   funcs.append({"query":q,"export":name,"rva":hex(address),"instructions":codes})
   print("\n",ver,q,"@",hex(address),flush=True)
   for x in codes:
    print(x["rva"],x["mnemonic"],x["operands"]," :: ".join(x["resolved_calls"])[:170],flush=True)
 report[ver]={"sha256":hashlib.sha256(raw).hexdigest(),"functions":funcs}
dest=root/"datasets/ae-native-shape-layer-command-type-adapter-2025-2026.json"
dest.write_text(json.dumps({"classification":"E2-L x64 disassembly of exact PE symbols with no AE runtime/private API execution",
"versions":report},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dest,flush=True)
