"""EXP-SHAPE-025 Focused native function disassembly: SVG paste async callback,
stream-path normalization, Root Vectors classification, vector art evaluation.
Only local pinned BEE2026 bytes; no host invocations.
"""
from pathlib import Path
import pefile,subprocess,re,json,bisect,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
root=Path(r"D:\Developer\After Effects Internals Guide")
path=Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")
p=pefile.PE(str(path));raw=path.read_bytes();base=p.OPTIONAL_HEADER.ImageBase
rx=re.compile(r"^\s*\d+\s+[0-9a-fA-F]+\s+([0-9a-fA-F]{8})\s+(\S+)")
syms={}
for line in subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,errors="replace",check=True).stdout.splitlines():
 m=rx.match(line)
 if m:syms[int(m.group(1),16)]=m.group(2)
imps={imp.address:desc.dll.decode(errors="replace")+"!"+imp.name.decode(errors="replace") for desc in p.DIRECTORY_ENTRY_IMPORT for imp in desc.imports if imp.name}
pdata=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in p.DIRECTORY_ENTRY_EXCEPTION)
starts=[i[0] for i in pdata]
functions={"svg_paste_command_callback":0x57e400,
           "svg_paste_target_layer_cleanup":0x57e790,
           "generic_find_contents_group":0x70b660,
           "contents_classifier":0x726de0,
           "native_vectorart_getter":0x7081b0,
           "svg_paste_command":0x57e210}
dec=Cs(CS_ARCH_X86,CS_MODE_64);dec.detail=True
data={}
for name,at in functions.items():
 index=bisect.bisect_right(starts,at)-1
 if index<0 or at>=pdata[index][1]:
  print(name,"no pdata");continue
 a,b=pdata[index]
 ops=[];calls=[]
 for ins in dec.disasm(raw[p.get_offset_from_rva(a):p.get_offset_from_rva(a)+(b-a)],base+a):
  rec={"at":hex(ins.address-base),"opcode":ins.mnemonic,"operand":ins.op_str}
  if ins.mnemonic in ("call","jmp") and ins.operands:
   arg=ins.operands[0]
   v=None
   if arg.type==X86_OP_IMM:v=arg.imm
   elif arg.type==X86_OP_MEM and arg.mem.base==X86_REG_RIP:v=ins.address+ins.size+arg.mem.disp
   rec["resolved"]=syms.get(v-base,"") or imps.get(v,"") if v is not None else ""
   if v is not None and v-base in functions.values():rec["note"]="TARGET_AUDITED"
   calls.append(rec)
  if "rip" in ins.op_str:
   for operand in ins.operands:
    if operand.type==X86_OP_MEM and operand.mem.base==X86_REG_RIP:
     disp=ins.address+ins.size+operand.mem.disp-base
     sym=syms.get(disp,"")
     if sym:rec["referenced_constant"]=sym
  ops.append(rec)
 data[name]={"start":hex(a),"end":hex(b),"code_instructions":ops}
 print("\n===",name,hex(a),hex(b),len(ops),"INSTRUCTIONS",flush=True)
 for op in ops:
  if op.get("resolved") or op.get("referenced_constant"):
   print(op["at"],op["opcode"],op["operand"],"FUNC",op.get("resolved","")[:190],
         "DATA",op.get("referenced_constant","")[:170],flush=True)
out=root/"datasets/ae-svg-contents-owner-async-callback-and-find-2026.json"
out.write_text(json.dumps({"classification":"E2-L native code disassembly x64 .pdata; exact binary only, not runtime plugin API","BEE_sha256":hashlib.sha256(raw).hexdigest(),"functions":data},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",out,flush=True)
