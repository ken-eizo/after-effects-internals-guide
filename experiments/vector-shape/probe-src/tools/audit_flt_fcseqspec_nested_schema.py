"""Offline AE2025/26 nested native Effect parameter schema audit.
Read TDB::StreamGroup::CanStore and FLT_FCSeqSpec::FillInCanonicalUILayout;
never invoke any Adobe code.
"""
from pathlib import Path
import pefile,json,hashlib,bisect
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
files={
"2025":{"TDB":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\TDB.dll",
        "FLT":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\FLT.dll"},
"2026":{"TDB":r"D:\Adobe\Adobe After Effects 2026\Support Files\TDB.dll",
        "FLT":r"D:\Adobe\Adobe After Effects 2026\Support Files\FLT.dll"}}
q={"TDB":["?CanStore@TDB_StreamGroup@@",
          "?SetupCanonicalLayout@TDB_StreamGroup@@",
          "?FillInStreamsFromCanonicalLayout@TDB_NamedStreamGroup@@"],
   "FLT":["?FillInCanonicalUILayout@FLT_FCSeqSpec@@",
          "?FillInCanonicalUILayout@FLT_EffectBuiltInParams@@",
          "?FillInCanonicalUILayout@FLT_CompoundEffect@@",
          "?Create@FLT_FCSeqSpec@@"]}
out={}
for year,items in files.items():
 out[year]={}
 for mod,path in items.items():
  buf=Path(path).read_bytes();pe=pefile.PE(data=buf);base=pe.OPTIONAL_HEADER.ImageBase
  syms={e.address:e.name.decode(errors="replace") for e in pe.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
  rs=sorted((a.struct.BeginAddress,a.struct.EndAddress) for a in pe.DIRECTORY_ENTRY_EXCEPTION)
  starts=[x[0] for x in rs]
  imports={i.address:desc.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace")
           for desc in pe.DIRECTORY_ENTRY_IMPORT for i in desc.imports if i.name}
  md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
  funcs=[]
  for prefix in q[mod]:
   hits=[(r,n) for r,n in syms.items() if n.startswith(prefix)]
   assert len(hits)==1,(year,mod,prefix,hits)
   entry,name=hits[0];pos=bisect.bisect_right(starts,entry)-1
   has_pdata=(pos>=0 and entry<rs[pos][1])
   # A trivial leaf virtual method may be a single RET and have no .pdata.
   stop=min(rs[pos][1],entry+14000) if has_pdata else entry+32
   instructions=[];edges=[]
   for ins in md.disasm(buf[pe.get_offset_from_rva(entry):pe.get_offset_from_rva(stop)],base+entry):
    if not has_pdata and ins.mnemonic in ("int3","nop"):break
    if len(instructions)<200:instructions.append({"rva":hex(ins.address-base),"m":ins.mnemonic,"args":ins.op_str})
    if not has_pdata and ins.mnemonic=="ret":break
    target=None
    if ins.mnemonic in ("call","jmp") and ins.operands:
     op=ins.operands[0]
     if op.type==X86_OP_IMM:target=op.imm
     elif op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
      target=ins.address+ins.size+op.mem.disp
    if target is not None:
     edges.append({"site":hex(ins.address-base),"operand":ins.op_str,
       "symbol":imports.get(target) or syms.get(target-base,""),"target_rva":hex(target-base)})
   funcs.append({"name":name,"entry":hex(entry),"end":hex(stop),
                 "instructions":instructions,"edges":edges})
   print(year,mod,name.split("@")[0],hex(entry),"instructions",len(instructions),
         "edges",len(edges),flush=True)
   for e in edges[:20]:print("  ",e["site"],e["symbol"][:125] or e["target_rva"],flush=True)
  out[year][mod]={"sha256":hashlib.sha256(buf).hexdigest(),"functions":funcs}
dest=Path(r"D:\Developer\ShapeLayerAE\results\flt_fcseqspec_nested_schema_2025_2026.json")
dest.write_text(json.dumps({"evidence":"E2-L static FLT/TDB native nested child contract; no runtime integration","versions":out},indent=2)+"\n")
print("SAVED",dest)
