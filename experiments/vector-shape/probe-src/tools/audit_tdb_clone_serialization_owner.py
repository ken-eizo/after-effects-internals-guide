"""EXP-SHAPE-025: Native TDB stream clone, save, load, and ownership ABI audit.

Deterministic, read-only: PE exports + x64 .pdata bounded disassembly.
Does not launch, patch, hook, or call After Effects. Stores finite named call
edges and virtual dispatch locations, not proprietary code bodies.
"""
import bisect,hashlib,json,re,subprocess
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_OP_IMM,X86_REG_RIP
BINS={
"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\TDB.dll"),
"2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\TDB.dll")}
ROOT=Path(r"D:\Developer\After Effects Internals Guide")
QUERIES={
"clone_base":"?Clone@TDB_StreamBase@@",
"clone_leaf":"?CloneStream@TDB_Stream@@",
"clone_parampath":"?CloneStream@TDB_ParamPathStream@@",
"read_base":"?Read@TDB_StreamBase@@",
"write_base":"?Write@TDB_StreamBase@@",
"read_group":"?Read@TDB_StreamGroup@@",
"write_group":"?Write@TDB_StreamGroup@@",
"read_leaf":"?Read@TDB_Stream@@",
"write_leaf":"?Write@TDB_Stream@@",
"parent_base":"?SetParent@TDB_StreamBase@@",
"find_editable":"?FindEditableStream@TDB_StreamGroup@@",
"canonical_layout":"?SetupCanonicalLayout@TDB_StreamGroup@@",
"indexed_append":"?AppendStream@TDB_IndexedStreamGroup@@",
}
PAT=re.compile(r"^\s*\d+\s+[a-fA-F0-9]+\s+([a-fA-F0-9]{8})\s+(\S+)")
all_data={}
for ver,path in BINS.items():
 data=path.read_bytes();pe=pefile.PE(data=data);base=pe.OPTIONAL_HEADER.ImageBase
 syms={}
 raw_exports=subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,errors="replace",check=True).stdout
 for line in raw_exports.splitlines():
  m=PAT.match(line)
  if m:syms[int(m.group(1),16)]=m.group(2)
 iat={i.address:e.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace")
      for e in pe.DIRECTORY_ENTRY_IMPORT for i in e.imports if i.name}
 pdata=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in pe.DIRECTORY_ENTRY_EXCEPTION)
 starts=[x[0] for x in pdata]
 cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
 rec={}
 for key,query in QUERIES.items():
  matches=sorted((rva,s) for rva,s in syms.items() if s.startswith(query))
  if len(matches)!=1:
   rec[key]={"match_count":len(matches),"candidate_names":[m[1] for m in matches[:4]]}
   continue
  addr,sym=matches[0]
  ix=bisect.bisect_right(starts,addr)-1
  if ix<0 or addr>=pdata[ix][1]:
   rec[key]={"export":sym,"rva":hex(addr),"note":"not bounded"}
   continue
  end=pdata[ix][1]
  if end-addr>24000:
   rec[key]={"export":sym,"rva":hex(addr),"note":"function exceeds audit bound"}
   continue
  calls=[]
  vt=[]
  comparisons=[]
  for ins in cs.disasm(data[pe.get_offset_from_rva(addr):pe.get_offset_from_rva(end)],base+addr):
   site=hex(ins.address-base)
   if ins.mnemonic in ("call","jmp") and ins.operands:
    op=ins.operands[0];target=None
    if op.type==X86_OP_IMM:target=op.imm
    elif op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:target=ins.address+ins.size+op.mem.disp
    symbol=syms.get(target-base) or iat.get(target,"") if target else ""
    calls.append({"site":site,"opcode":ins.mnemonic,"target_rva":hex(target-base) if target else None,
                  "resolved":symbol, "indirect":target is None,
                  "op":ins.op_str if target is None else ""})
    if op.type==X86_OP_MEM and op.mem.base!=X86_REG_RIP and op.mem.disp and target is None:
     vt.append({"site":site,"register":ins.reg_name(op.mem.base),"byte_offset":hex(op.mem.disp)})
   if ins.mnemonic in ("cmp","test") and len(comparisons)<35:
    comparisons.append({"site":site,"opcode":ins.mnemonic,"op":ins.op_str})
  rec[key]={"export":sym,"rva":hex(addr),"bounded_bytes":end-addr,
            "resolved_calls":[c for c in calls if c["resolved"]],
            "indirect_virtual_calls":vt,
            "unresolved_direct_call_count":sum(not c["resolved"] and not c["indirect"] for c in calls),
            "all_call_count":len(calls),
            "comparisons_first35":comparisons}
  print(ver,key,hex(addr),"bytes",end-addr,"calls",len(calls),"virt",len(vt),
        "resolved",[(x["site"],x["resolved"][:55]) for x in rec[key]["resolved_calls"][:9]],flush=True)
 all_data[ver]={"tdb_sha256":hashlib.sha256(data).hexdigest(),"methods":rec}
out=ROOT/"datasets/ae-tdb-native-clone-serialization-parent-callgraph-2025-2026.json"
out.write_text(json.dumps({"classification":"E2-L, read-only local native x64 DLL callgraph and bounds; no verified external ABI",
 "versions":all_data},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",out,flush=True)
