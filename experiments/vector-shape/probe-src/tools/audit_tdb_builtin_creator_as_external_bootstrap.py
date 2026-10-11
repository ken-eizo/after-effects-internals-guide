"""EXP-SHAPE-027 read-only ABI feasibility of a native-class-backed new TDB type.

Trace Adobe's built-in TDB_ParamPathStream::Create (known complete class) and
TDB_MatchName(const char*,bool). If a future third-party type-registration
experiment is ever attempted, native creation may be safer than inventing a
partially initialized TDB_StreamBase. This script NEVER executes private APIs.
"""
from pathlib import Path
from bisect import bisect_right
import json,subprocess,hashlib,re,pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
ROOT=Path(r"D:\Developer\After Effects Internals Guide")
bins={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\TDB.dll"),
      "2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\TDB.dll")}
queries={
"native_path_create":"?Create@TDB_ParamPathStream@@",
"native_layer_param_create":"?Create@TDB_ParamLayerStream@@",
"native_path_ctor":"??0TDB_ParamPathStream@@QEAA@IEPEBVTDB_MatchName@@",
"matchname_from_chars":"??0TDB_MatchName@@QEAA@PEBD_N@Z",
"matchname_copy":"??0TDB_MatchName@@QEAA@AEBV0@@Z",
"native_indexed_group_ctor":"??0TDB_IndexedStreamGroup@@QEAA@PEBVTDB_MatchName@@",
"native_stream_base_ctor":"??0TDB_StreamBase@@QEAA@PEBVTDB_MatchName@@",
"native_sc_register":"?Register@TDB_ScRegisterStreams@@",
"native_factory_register":"?RegisterFactoryFunc@TDB_StreamFactory@@",
}
pattern=re.compile(r"^\s*\d+\s+[0-9a-fA-F]+\s+([0-9a-fA-F]{8})\s+(\S+)")
result={}
for ver,path in bins.items():
 blob=path.read_bytes();pe=pefile.PE(data=blob);base=pe.OPTIONAL_HEADER.ImageBase
 exports={}
 for line in subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,errors="replace",check=True).stdout.splitlines():
  m=pattern.match(line)
  if m:exports[int(m.group(1),16)]=m.group(2)
 imports={i.address:e.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace")
          for e in pe.DIRECTORY_ENTRY_IMPORT for i in e.imports if i.name}
 fs=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in pe.DIRECTORY_ENTRY_EXCEPTION)
 starts=[x[0] for x in fs]
 md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
 functions={}
 for key,q in queries.items():
  hits=[(r,s) for r,s in exports.items() if s.startswith(q)]
  if len(hits)!=1:
   functions[key]={"found_count":len(hits)}
   continue
  rva,name=hits[0];ix=bisect_right(starts,rva)-1
  if ix<0 or rva>=fs[ix][1]:raise ValueError((ver,key,hex(rva)))
  start,end=fs[ix];summary={"entry_rva":hex(rva),"size_bytes":end-start,"symbol":name}
  insns=[];calls=[]
  for j,ins in enumerate(md.disasm(blob[pe.get_offset_from_rva(rva):pe.get_offset_from_rva(end)],base+rva)):
   if j<30:insns.append({"site":hex(ins.address-base),"opcode":ins.mnemonic,"operands":ins.op_str})
   if ins.mnemonic in ("call","jmp"):
    target=None
    if ins.operands:
     op=ins.operands[0]
     if op.type==X86_OP_IMM:target=op.imm
     elif op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:target=ins.address+ins.size+op.mem.disp
    if target:
     sym=exports.get(target-base) or imports.get(target,"")
     calls.append({"site":hex(ins.address-base),"target_rva":hex(target-base),"symbol":sym})
  summary.update({"first30_instructions":insns,"symbolized_calls":calls})
  functions[key]=summary
  print(ver,key,"RVA",hex(rva),"len",end-start,"calls",
    [(x["site"],x["symbol"][:68]) for x in calls if x["symbol"]][:9],flush=True)
 result[ver]={"TDB_sha256":hashlib.sha256(blob).hexdigest(),"functions":functions}
out=ROOT/"datasets/ae-native-tdb-built-in-path-creator-registration-feasibility-2025-2026.json"
out.write_text(json.dumps({
"classification":"E2-L read-only, Native Creator registration feasibility, NOT third-party registration proof",
"versions":result},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",out,flush=True)
