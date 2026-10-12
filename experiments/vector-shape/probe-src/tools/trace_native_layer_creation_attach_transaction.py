"""Recover native layer creation -> attachment transaction candidate code paths.
PE/.pdata-bound disassembly, precise callsite checks, adjacent x64 instruction dataflow.
No Adobe process execution or library invocation.
"""
from pathlib import Path
import bisect, pefile, json, hashlib
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86_const import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP
cfg={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",[0x3a7ca0,0x3a9b90,0x3acbf0,0x505090,0x505400,0x392120,0x65cb40,0x65cdd0]),
     "2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",[0x3b4110,0x3b60b0,0x3b8fd0,0x51f2f0,0x51f650,0x39d4d0,0x678160,0x6783e0])}
results={}
for y,(file,candidates) in cfg.items():
 b=Path(file).read_bytes()
 p=pefile.PE(data=b);base=p.OPTIONAL_HEADER.ImageBase
 names={x.address:x.name.decode(errors="replace") for x in p.DIRECTORY_ENTRY_EXPORT.symbols if x.name}
 imp={i.address:m.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace") for m in p.DIRECTORY_ENTRY_IMPORT for i in m.imports if i.name}
 pdata=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION);starts=[t[0] for t in pdata]
 dec=Cs(CS_ARCH_X86,CS_MODE_64);dec.detail=True
 infos={}
 for target in candidates:
  j=bisect.bisect_right(starts,target)-1
  if j>=0 and target<pdata[j][1]:a,z=pdata[j]
  else:a,z=target,target+150 # exported thin stub lacks its own pdata
  instructions=list(dec.disasm(b[p.get_offset_from_rva(a):p.get_offset_from_rva(z)],base+a))
  calls=[];allinst=[]
  for k,x in enumerate(instructions):
   r={"rva":hex(x.address-base),"instr":x.mnemonic+" "+x.op_str}
   allinst.append(r)
   if x.mnemonic not in ("call","jmp") or not x.operands:continue
   op=x.operands[0];to=None
   if op.type==X86_OP_IMM:to=op.imm
   if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:to=x.address+x.size+op.mem.disp
   name=(imp.get(to) or names.get(to-base,"")) if to is not None else ""
   bef=[{"rva":hex(t.address-base),"instr":t.mnemonic+" "+t.op_str} for t in instructions[max(k-12,0):k]]
   calls.append({"site":hex(x.address-base),"target_rva":hex(to-base) if to else "", "export":name,"immediate_context":bef})
  info={"name":names.get(a,""),"code_start":hex(a),"code_end":hex(z),"calls":calls,
        "all_instructions":allinst}
  infos[hex(a)]=info
  matches=[c for c in calls if any(s in c["export"] for s in ("CreateLayerFromType","AttachLayerToComp","BEE_CmdNewLayer","BEE_VectorLayer"))]
  print(y,hex(a),"bytes",z-a,"allcalls",len(calls),"owner-critical",len(matches),flush=True)
  for m in matches: print("  ",m["site"],m["export"],"near",m["immediate_context"][-6:],flush=True)
 results[y]={"BEE_sha256":hashlib.sha256(b).hexdigest(),"functions":infos}
p=Path(r"D:\Developer\ShapeLayerAE\results\bee_layer_creation_attach_transaction_contexts_2025_2026.json")
p.write_text(json.dumps({"evidence":"E2-L BEE.dll 2025/26 p-data function bounded x64 disassembly with exactly-resolved callsite signatures", "versions":results},indent=2)+"\n")
print("SAVED",p)
