"""Trace the Adobe native TDB stream wrapping PUBLIC Effect ARBITRARY_DATA,
including FLT sequence->parameter-stream lookup and C++ cloned value owners.
STATIC pinned AE2025/AE2026 FLT.dll only; no private invocation.
"""
from pathlib import Path
import pefile,bisect,json,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
bins={
"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\FLT.dll",
"2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\FLT.dll"}
prefixes={
"seq_param_stream":"?FLT_SeqInqParamStream@@",
"arb_create":"?Create@FLT_ParamArbDataStream@@",
"arb_clone":"?CloneStream@FLT_ParamArbDataStream@@",
"arb_ctor":"??0FLT_ParamArbDataStream@@QEAA@IE",
"arb_dispose":"?DisposeValue@FLT_ParamArbDataStream@@",
"arb_print":"?FLT_ArbitraryPrint@@",
"arb_print_size":"?FLT_ArbitraryPrintSize@@",
"arb_scan":"?FLT_ArbitraryScan@@",
"arb_delete":"?DeleteArbDataItem@FLT_ParamArbDataStream@@"
}
out={}
for ver,file in bins.items():
 raw=Path(file).read_bytes();pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase
 syms={e.name.decode(errors="replace"):e.address for e in pe.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 rev={v:k for k,v in syms.items()}
 imported={i.address:ds.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace") for ds in pe.DIRECTORY_ENTRY_IMPORT for i in ds.imports if i.name}
 regions=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in pe.DIRECTORY_ENTRY_EXCEPTION);start=[a for a,b in regions]
 d=Cs(CS_ARCH_X86,CS_MODE_64);d.detail=True
 info={}
 for key,prefix in prefixes.items():
  matches=[(n,r) for n,r in syms.items() if n.startswith(prefix)]
  assert len(matches)==1,(ver,key,matches)
  name,rva=matches[0]
  idx=bisect.bisect_right(start,rva)-1
  pdata=idx>=0 and rva<regions[idx][1]
  end=min(regions[idx][1],rva+9000) if pdata else rva+72
  ins=[];edges=[]
  for i in d.disasm(raw[pe.get_offset_from_rva(rva):pe.get_offset_from_rva(end)],base+rva):
   row={"rva":hex(i.address-base),"op":i.mnemonic,"args":i.op_str}
   target=None
   if i.mnemonic in ("call","jmp") and i.operands:
    q=i.operands[0]
    if q.type==X86_OP_IMM:target=q.imm
    elif q.type==X86_OP_MEM and q.mem.base==X86_REG_RIP:target=i.address+i.size+q.mem.disp
   if target is not None:
    row["callee"]=rev.get(target-base) or imported.get(target,"")
    row["target"]=hex(target-base)
    edges.append(row)
   if len(ins)<190:ins.append(row)
   if not pdata and i.mnemonic=="ret":break
  info[key]={"export":name,"start":hex(rva),"end":hex(end),"has_pdata":pdata,
             "instructions":ins,"edges":edges}
  print(ver,key,hex(rva),"calls",len(edges),flush=True)
  for e in edges[:14]:print(" ",e["rva"],e["callee"][:112] or e["target"],flush=True)
 vt=[(n,r) for n,r in syms.items() if n.startswith("??_7FLT_ParamArbDataStream@@6B@")]
 assert len(vt)==1
 out[ver]={"sha256":hashlib.sha256(raw).hexdigest(),"arbitrary_vtable":vt[0],
           "methods":info}
dest=Path(r"D:\Developer\ShapeLayerAE\results\flt_effect_arbitrary_tdb_stream_bridge_2025_2026.json")
dest.write_text(json.dumps({"evidence":"E2-L pinned FLT machine code for public arbitrary Effect type's native wrapper; runtime behavior untested","versions":out},indent=2)+"\n")
print("SAVED",dest)
