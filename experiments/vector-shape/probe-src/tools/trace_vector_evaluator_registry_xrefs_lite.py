"""Memory-bounded vector evaluator registry xref scan via Capstone disasm_lite.
Static PE sections only; no private API execution.
"""
import pefile,subprocess,re,json,bisect,hashlib,gc
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
paths={
"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
 {"accessor":0x6f87e0,"lookup":0x6f9020,"dispatch":0x6ecd40,"insert_accessor":0x6f88c0,"registry_construct":0x6eef40,"register_evaluator":0x6eeb20,"global":0x6f87eb+0xef6bfd}),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",
 {"accessor":0x71c2f0,"lookup":0x71cc00,"dispatch":0x711040,"insert_accessor":0x71c3d0,"registry_construct":0x713550,"register_evaluator":0x713120,"global":0x71c2fb+0xf83abd})}
rx=re.compile(r"^\s*(\d+)\s+([0-9A-Fa-f]+)\s+([0-9A-Fa-f]{8})\s+(\S+)")
rip=re.compile(r"\[rip\s*([+-])\s*0x([0-9A-Fa-f]+)\]")
res={}
for ver,(file,targets) in paths.items():
 p=pefile.PE(file,fast_load=True)
 p.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXCEPTION"]])
 base=p.OPTIONAL_HEADER.ImageBase
 exports={}
 for line in subprocess.run(["dumpbin","/exports",file],capture_output=True,text=True,errors="replace").stdout.splitlines():
  match=rx.match(line)
  if match:exports[int(match.group(3),16)]=match.group(4)
 ex=sorted(exports)
 functions=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION)
 starts=[x[0] for x in functions]
 decoder=Cs(CS_ARCH_X86,CS_MODE_64)
 decoder.skipdata=True
 hits={k:[] for k in targets}
 scanned=0
 for section in p.sections:
  if not section.Characteristics & 0x20000000:continue
  raw=section.get_data()
  for addr,size,op,arg in decoder.disasm_lite(raw,base+section.VirtualAddress):
   scanned+=1
   at=addr-base
   dst=None
   if op in ("call","jmp") and arg.startswith("0x"):
    try:dst=int(arg,16)-base
    except ValueError:pass
   elif "rip" in arg:
    m=rip.search(arg)
    if m:
     disp=int(m.group(2),16)*(1 if m.group(1)=="+" else -1)
     dst=at+size+disp
   if dst is None:continue
   for key,t in targets.items():
    if dst!=t:continue
    ix=bisect.bisect_right(starts,at)-1
    start=starts[ix] if ix>=0 and at<functions[ix][1] else None
    exi=bisect.bisect_right(ex,start)-1 if start is not None else -1
    hits[key].append({"at":hex(at),"mnemonic":op,"operands":arg,"function_start":hex(start) if start is not None else "",
                      "nearest_export_hypothesis":exports[ex[exi]] if exi>=0 else ""})
 del raw
 print(ver,"scanned",scanned,{k:len(v) for k,v in hits.items()},flush=True)
 for k,v in hits.items():
  for x in v[:45]:
   print(" ",k,x["at"],x["mnemonic"],x["function_start"],x["nearest_export_hypothesis"][:100],flush=True)
 res[ver]={"scanned_instructions":scanned,"targets":targets,"matches":hits}
 del p
 gc.collect()
out=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-vector-evaluator-registry-xrefs-2025-2026.json")
out.write_text(json.dumps({"classification":"E2-L; bounded static PE scan using low-memory disasm_lite","versions":res},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",out,flush=True)
