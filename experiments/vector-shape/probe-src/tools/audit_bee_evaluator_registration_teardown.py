"""EXP-SHAPE-026 read-only private BEE native vector evaluator registry lifecycle.

Bounded x64 disassembly of selected proven registry construction, registration,
lookup, accessor and shutdown code, using actual installed AE DLLs.
No Adobe functions are run, no host memory touched.
"""
import bisect,hashlib,json,re,subprocess
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
BINS={
"2025":(Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
 {"reg":0x6eeb20,"ctor":0x6eef40,"lookup":0x6f9020,
  "accessor":0x6f87e0,"post_init":0x6eefb0,"destruct_hint":0x6fdccb}),
"2026":(Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"),
 {"reg":0x713120,"ctor":0x713550,"lookup":0x71cc00,
  "accessor":0x71c2f0,"post_init":0x7135b9,"destruct_hint":0x7217cb})
}
ROOT=Path(r"D:\Developer\After Effects Internals Guide")
PAT=re.compile(r"^\s*\d+\s+[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s+(\S+)")
report={}
for ver,(path,target) in BINS.items():
 raw=path.read_bytes();pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase
 syms={}
 for line in subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,errors="replace",check=True).stdout.splitlines():
  m=PAT.match(line)
  if m:syms[int(m.group(1),16)]=m.group(2)
 imp={i.address:e.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace")
       for e in pe.DIRECTORY_ENTRY_IMPORT for i in e.imports if i.name}
 pdata=sorted((i.struct.BeginAddress,i.struct.EndAddress) for i in pe.DIRECTORY_ENTRY_EXCEPTION)
 starts=[i[0] for i in pdata]
 md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
 funcs={}
 for label,rva in target.items():
  ix=bisect.bisect_right(starts,rva)-1
  if ix<0 or rva>=pdata[ix][1]:raise RuntimeError((ver,label,hex(rva)))
  a,b=pdata[ix]
  calls=[];virtual=[];memory=[];cmp=[]
  for ins in md.disasm(raw[pe.get_offset_from_rva(a):pe.get_offset_from_rva(b)],base+a):
   site=hex(ins.address-base)
   if ins.mnemonic in ("call","jmp") and ins.operands:
    o=ins.operands[0];dest=None
    if o.type==X86_OP_IMM:dest=o.imm
    elif o.type==X86_OP_MEM and o.mem.base==X86_REG_RIP:dest=ins.address+ins.size+o.mem.disp
    names=syms.get(dest-base) or imp.get(dest,"") if dest else ""
    calls.append({"site":site,"target_rva":hex(dest-base) if dest else "",
     "target":names,"indirect":dest is None,"op":ins.mnemonic+" "+ins.op_str})
    if dest is None and o.type==X86_OP_MEM:
     virtual.append({"site":site,"base_reg":ins.reg_name(o.mem.base),"disp":hex(o.mem.disp)})
   if ins.mnemonic in ("lea","mov") and len(ins.operands)>=2:
    o=ins.operands[-1]
    if o.type==X86_OP_MEM and o.mem.base==X86_REG_RIP and len(memory)<100:
     memory.append({"site":site,"rva":hex(ins.address+ins.size+o.mem.disp-base),
                   "mnemonic":ins.mnemonic,"op":ins.op_str})
   if ins.mnemonic in ("cmp","test") and len(cmp)<65:cmp.append({"site":site,"op":ins.mnemonic+" "+ins.op_str})
  funcs[label]={"function_start":hex(a),"function_end":hex(b),"bytes":b-a,
    "first65_comparisons":cmp,"calls":calls,"virtual_calls":virtual,"references_to_global_data":memory}
  print(ver,label,hex(a),"BYTES",b-a,"calls",len(calls),"virtual",len(virtual),flush=True)
  for c in calls:
   if c["target"]:print("  ",c["site"],c["target"][:105],flush=True)
 report[ver]={"BEE_sha256":hashlib.sha256(raw).hexdigest(),"code":funcs}
out=ROOT/"datasets/ae-bee-evaluator-register-shutdown-callback-abi-2025-2026.json"
out.write_text(json.dumps({"classification":"E2-L private native BEE registry static PE disassembly; function names are analytical labels, not public ABI", "versions":report},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",out,flush=True)
