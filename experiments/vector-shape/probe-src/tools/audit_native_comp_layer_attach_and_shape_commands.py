"""Find exact BEE Layer creation / Comp attachment transactions.
Read-only static x64 disassembly of real AE2025/2026 BEE native functions.
"""
from pathlib import Path
import pefile,json,bisect,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
cfg={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
     "2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
markers=["?AttachLayerToCompAndLayerParamsOnly@BEE_CompItem@@",
"?AttachLayerToCompOnly@BEE_CompItem@@",
"?BEE_CmdNewLayer@@",
"?BEE_CmdNewVectorLayer@@"]
out={}
for year,file in cfg.items():
 data=Path(file).read_bytes();pe=pefile.PE(data=data);base=pe.OPTIONAL_HEADER.ImageBase
 exp={e.name.decode(errors="replace"):e.address for e in pe.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 names={v:k for k,v in exp.items()}
 imp={x.address:d.dll.decode(errors="replace")+"!"+x.name.decode(errors="replace")
      for d in pe.DIRECTORY_ENTRY_IMPORT for x in d.imports if x.name}
 ranges=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in pe.DIRECTORY_ENTRY_EXCEPTION)
 start=[a for a,b in ranges]
 d=Cs(CS_ARCH_X86,CS_MODE_64);d.detail=True
 methods={}
 for marker in markers:
  candidates=[(s,rva) for s,rva in exp.items() if s.startswith(marker)]
  assert len(candidates)==1,(year,marker,candidates)
  name,rva=candidates[0]
  k=bisect.bisect_right(start,rva)-1
  if k>=0 and rva<ranges[k][1]:
   a,b=ranges[k]
  else:a,b=rva,rva+150
  ins=list(d.disasm(data[pe.get_offset_from_rva(a):pe.get_offset_from_rva(b)],base+a))
  calls=[];first=[]
  for x in ins:
   row={"rva":hex(x.address-base),"op":x.mnemonic,"args":x.op_str}
   if len(first)<135:first.append(row)
   if x.mnemonic not in ("call","jmp") or not x.operands:continue
   op=x.operands[0];ptr=None
   if op.type==X86_OP_IMM:ptr=op.imm
   if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:ptr=x.address+x.size+op.mem.disp
   if ptr is not None:row["target"]=imp.get(ptr) or names.get(ptr-base,"")
   calls.append(row)
  methods[marker]={"export":name,"entry_rva":hex(rva),"begin":hex(a),"end":hex(b),
    "instructions":first,"calls":calls}
  print(year,marker,"RVA",hex(rva),"FUNC_SIZE",b-a,"CALLS",len(calls),flush=True)
  for x in calls[:40]:print(" ",x["rva"],x.get("target","")[:145],x["op"],x["args"],flush=True)
 out[year]={"BEE_sha256":hashlib.sha256(data).hexdigest(),"methods":methods}
dest=Path(r"D:\Developer\ShapeLayerAE\results\bee_native_comp_layer_attach_and_new_shape_command_2025_2026.json")
dest.write_text(json.dumps({"evidence":"E2-L installed AE2025/26 BEE native exported attach + NewLayer/VectorLayer command disassembly, no host invocation",
"versions":out},indent=2)+"\n")
print("SAVED",dest)
