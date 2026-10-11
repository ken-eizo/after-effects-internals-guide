"""Native TDB_ScRegisterStreams destructor/registration lifetime audit.
Exact installed TDB.dll PE code only; no native API executed.
"""
from pathlib import Path
import pefile,bisect,hashlib,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
files={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\TDB.dll",
       "2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\TDB.dll"}
names={
"constructor":"??0TDB_ScRegisterStreams@@QEAA@PEAVTDB_StreamFactory@@",
"destructor":"??1TDB_ScRegisterStreams@@QEAA@XZ",
"register":"?Register@TDB_ScRegisterStreams@@",
"unregister_all":"?UnregisterAll@TDB_ScRegisterStreams@@",
"factory_unregister":"?UnregisterFactoryFunc@TDB_StreamFactory@@"}
out={}
for year,fn in files.items():
 data=Path(fn).read_bytes();p=pefile.PE(data=data);base=p.OPTIONAL_HEADER.ImageBase
 exports={s.name.decode(errors="replace"):s.address for s in p.DIRECTORY_ENTRY_EXPORT.symbols if s.name}
 syms={v:k for k,v in exports.items()}
 imported={s.address:lib.dll.decode(errors="replace")+"!"+s.name.decode(errors="replace")
           for lib in p.DIRECTORY_ENTRY_IMPORT for s in lib.imports if s.name}
 bounds=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in p.DIRECTORY_ENTRY_EXCEPTION)
 begins=[a for a,b in bounds];cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
 methods={}
 for kind,prefix in names.items():
  cand=[(k,v) for k,v in exports.items() if k.startswith(prefix)]
  assert len(cand)==1,(year,kind,cand)
  name,rva=cand[0]
  ix=bisect.bisect_right(begins,rva)-1
  valid=ix>=0 and rva<bounds[ix][1]
  end=min(bounds[ix][1],rva+7000) if valid else rva+160
  rows=[];calls=[]
  for x in cs.disasm(data[p.get_offset_from_rva(rva):p.get_offset_from_rva(end)],base+rva):
   row={"rva":hex(x.address-base),"m":x.mnemonic,"args":x.op_str}
   target=None
   if x.mnemonic in ("call","jmp") and x.operands:
    op=x.operands[0]
    if op.type==X86_OP_IMM:target=op.imm
    elif op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
     target=x.address+x.size+op.mem.disp
   if target is not None:
    row["target"]=hex(target-base)
    row["symbol"]=syms.get(target-base) or imported.get(target,"")
    calls.append(row)
   rows.append(row)
   if not valid and x.mnemonic=="ret":break
  methods[kind]={"entry":hex(rva),"end":hex(end),"unwind_bounded":valid,
                 "ops":rows[:300],"edges":calls}
  print("YEAR",year,kind,hex(rva),"calls",len(calls),flush=True)
  for e in calls[:22]:print(" ",e["rva"],e.get("symbol") or e["target"],flush=True)
 out[year]={"sha256":hashlib.sha256(data).hexdigest(),"methods":methods}
dst=Path(r"D:\Developer\ShapeLayerAE\results\tdb_scoped_registry_lifetime_abi_2025_2026.json")
dst.write_text(json.dumps({"evidence":"E2-L scoped registry C++ destructor/registration native code, no host operation","versions":out},indent=2)+"\n",encoding="utf8")
print("SAVED",dst)
