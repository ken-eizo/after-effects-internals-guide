"""EXP-SHAPE-024 Locate read-only RIP-relative references to native vector owner
Root Vectors and Contents MatchName constants, with caller .pdata context.
No private function called, no process memory read.
"""
from pathlib import Path
import pefile,re,json,subprocess,bisect,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
root=Path(r"D:\Developer\After Effects Internals Guide")
file=Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")
raw=file.read_bytes();pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase
rx=re.compile(r"^\s*\d+\s+[0-9a-fA-F]+\s+([0-9a-fA-F]{8})\s+(\S+)")
syms={}
for line in subprocess.run(["dumpbin","/exports",str(file)],capture_output=True,text=True,errors="replace",check=True).stdout.splitlines():
 m=rx.match(line)
 if m:syms[int(m.group(1),16)]=m.group(2)
patterns=["StreamName_ROOT_VECTORS_GROUP","StreamName_VECTORS_GROUP","StreamName_SHAPE_GROUP",
"StreamName_SHAPE","StreamName_GRAPHIC","StreamName_FILL","StreamName_STROKE",
"StreamName_VECTOR","StreamName_ROOT_VECTORS"]
targets={addr:name for addr,name in syms.items() if any(p in name for p in patterns)}
print("TARGETS",len(targets),flush=True)
for k,v in targets.items():print(hex(k),v[:160],flush=True)
pdata=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in pe.DIRECTORY_ENTRY_EXCEPTION)
starts=[x[0] for x in pdata]
decoder=Cs(CS_ARCH_X86,CS_MODE_64);decoder.skipdata=True
rip=re.compile(r"\[rip\s*([+-])\s*(0x[0-9a-fA-F]+)\]")
hits={addr:[] for addr in targets}
count=0
for sec in pe.sections:
 if not sec.Characteristics & 0x20000000:continue
 for va,size,opc,txt in decoder.disasm_lite(sec.get_data(),base+sec.VirtualAddress):
  count+=1
  if opc not in ("lea","mov","cmp","add","sub"):continue
  m=rip.search(txt)
  if not m:continue
  displacement=int(m.group(2),16)*(1 if m.group(1)=="+" else -1)
  pointer=va+size+displacement-base
  if pointer not in hits:continue
  at=va-base
  idx=bisect.bisect_right(starts,at)-1
  fn=starts[idx] if idx>=0 and at<pdata[idx][1] else None
  hits[pointer].append({"site":hex(at),"caller_function_start":hex(fn) if fn is not None else None,
   "caller_function_export":syms.get(fn,"") if fn is not None else "", "asm":opc+" "+txt})
data=[]
for addr,name in sorted(targets.items()):
 refs=hits[addr]
 print("\nREF",hex(addr),name[:95],"direct RIP users",len(refs),flush=True)
 for ref in refs[:60]:print(" ",ref["site"],ref["caller_function_start"],ref["caller_function_export"][:130],flush=True)
 data.append({"constant_rva":hex(addr),"symbol":name,"direct_rip_references":refs,"reference_count":len(refs)})
out=root/"datasets/ae-vector-root-contents-rip-ownership-xrefs-2026.json"
out.write_text(json.dumps({"classification":"E2-L direct RIP data refs to exported MatchName objects; not proof of runtime owner acceptance or third-party ABI","BEE_sha256":hashlib.sha256(raw).hexdigest(),"instructions_scanned":count,"results":data},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("SAVED",out,flush=True)
