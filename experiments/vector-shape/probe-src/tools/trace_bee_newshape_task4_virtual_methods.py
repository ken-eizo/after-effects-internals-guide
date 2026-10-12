"""Resolve the three virtual methods of BEE_NewLayerTask<4>,
and their exact native calls into Layer creation / Comp attach.
Offline BEE x64 2025+2026 only.
"""
from pathlib import Path
import pefile,bisect,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
p=Path(r"D:\Developer\ShapeLayerAE\results")
vt=json.loads((p/"bee_new_shape_command_object_rtti_vtable_2025_2026.json").read_text())["versions"]
bins={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
      "2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
out={}
for y,path in bins.items():
 pe=pefile.PE(path);blob=Path(path).read_bytes();base=pe.OPTIONAL_HEADER.ImageBase
 syms={e.address:e.name.decode(errors="replace") for e in pe.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 imps={i.address:d.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace") for d in pe.DIRECTORY_ENTRY_IMPORT for i in d.imports if i.name}
 pd=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in pe.DIRECTORY_ENTRY_EXCEPTION);begins=[a for a,b in pd]
 dis=Cs(CS_ARCH_X86,CS_MODE_64);dis.detail=True;funcs=[]
 for ent in vt[y]["virtual_methods"]:
  target=int(ent["function_rva"],16);k=bisect.bisect_right(begins,target)-1
  a,b=pd[k] if k>=0 and target<pd[k][1] else (target,target+200)
  ins=[];calls=[]
  for i in dis.disasm(blob[pe.get_offset_from_rva(a):pe.get_offset_from_rva(b)],base+a):
   row={"rva":hex(i.address-base),"op":i.mnemonic,"args":i.op_str}
   if len(ins)<120:ins.append(row)
   if i.mnemonic not in ("call","jmp") or not i.operands:continue
   q=i.operands[0];to=None
   if q.type==X86_OP_IMM:to=q.imm
   if q.type==X86_OP_MEM and q.mem.base==X86_REG_RIP:to=i.address+i.size+q.mem.disp
   if to is not None:row["target_rva"]=hex(to-base);row["target_symbol"]=syms.get(to-base) or imps.get(to,"")
   calls.append(row)
  print(y,"VIRTUAL",ent["slot"],hex(target),"range",hex(a),hex(b),"CALLS",len(calls),flush=True)
  for x in calls[:40]:print(" ",x,flush=True)
  funcs.append({"slot":ent["slot"],"entry_rva":hex(target),"range":[hex(a),hex(b)],"calls":calls,"first_instructions":ins})
 out[y]={"rtti_class":vt[y]["RTTI_Cpp_class_decorated"],"virtuals":funcs}
dst=p/"bee_newshape_task4_vtable_virtual_calltargets_2025_2026.json"
dst.write_text(json.dumps({"evidence":"E2-L pinned installed BEE virtual methods for actual New Shape task C++ class","versions":out},indent=2)+"\n")
print("SAVED",dst)
