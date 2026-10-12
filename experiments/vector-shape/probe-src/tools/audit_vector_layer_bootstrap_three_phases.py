"""Native Shape bootstrap: resolve the three phases of BEE_VectorLayer::RegisterStreams.
Pinned AE2025/26 binaries only; no AE host execution.
"""
from pathlib import Path
import pefile,bisect,hashlib,json,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
versions={
"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
    {"phase1":0x77c630,"phase2":0x6eef40,"phase3":0x6fdcc0}),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",
    {"phase1":0x79d040,"phase2":0x713550,"phase3":0x7217c0})
}
out={}
for ver,(file,targets) in versions.items():
 pe=pefile.PE(file);blob=Path(file).read_bytes();base=pe.OPTIONAL_HEADER.ImageBase
 syms={e.address:e.name.decode(errors="replace") for e in pe.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 imps={entry.address:desc.dll.decode(errors="replace")+"!"+entry.name.decode(errors="replace")
    for desc in pe.DIRECTORY_ENTRY_IMPORT for entry in desc.imports if entry.name}
 pdata=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in pe.DIRECTORY_ENTRY_EXCEPTION)
 starts=[x[0] for x in pdata]
 dis=Cs(CS_ARCH_X86,CS_MODE_64);dis.detail=True
 functions={}
 for label,rva in targets.items():
  i=bisect.bisect_right(starts,rva)-1
  assert i>=0 and rva<pdata[i][1],(ver,label,hex(rva))
  a,b=pdata[i]
  inst=[];calls=[];refs=[]
  for x in dis.disasm(blob[pe.get_offset_from_rva(a):pe.get_offset_from_rva(b)],base+a):
   item={"rva":hex(x.address-base),"op":x.mnemonic,"args":x.op_str}
   if x.operands:
    q=x.operands[-1]
    if q.type==X86_OP_MEM and q.mem.base==X86_REG_RIP:
     target=x.address+x.size+q.mem.disp
     item["rip_rva"]=hex(target-base)
     if x.mnemonic in ("call","jmp"):
      item["link"]=imps.get(target,syms.get(target-base,""))
    elif x.mnemonic in ("call","jmp") and q.type==X86_OP_IMM:
     item["link"]=syms.get(q.imm-base,"")
     item["target_rva"]=hex(q.imm-base)
   if x.mnemonic in ("call","jmp"):calls.append(item)
   if x.mnemonic in ("lea","mov") and "rip_rva" in item:refs.append(item)
   if len(inst)<210:inst.append(item)
  functions[label]={"rva":hex(rva),"start":hex(a),"end":hex(b),
    "code_bytes":b-a,"calls":calls,"rip_refs":refs[:110],"first_instructions":inst}
  print(ver,label,"size",b-a,"calls",len(calls),"imported",sum(bool(v.get("link")) for v in calls),flush=True)
  for row in calls[:90]:print("   ",row["rva"],row["args"],row.get("link","")[:180],flush=True)
 out[ver]={"hash_sha256":hashlib.sha256(blob).hexdigest(),"functions":functions}
dest=Path(r"D:\Developer\ShapeLayerAE\results\bee_vector_layer_registerstreams_three_phases_2025_2026.json")
dest.write_text(json.dumps({"kind":"E2-L pinned offline BEE x64 PE; not private runtime use","versions":out},indent=2)+"\n")
print("SAVED",dest)
