"""Verify generic TDB_StreamGroup CanStore scans allowed-child MatchNames.
TDB 2025/2026 static x64 machine code, no private method calls.
"""
from pathlib import Path
import hashlib,json,bisect,pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM
files={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\TDB.dll",
"2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\TDB.dll"}
out={}
for year,fn in files.items():
 data=Path(fn).read_bytes();p=pefile.PE(data=data);base=p.OPTIONAL_HEADER.ImageBase
 syms={s.name.decode(errors="replace"):s.address for s in p.DIRECTORY_ENTRY_EXPORT.symbols if s.name}
 ex={r:n for n,r in syms.items()}
 entry=syms["?CanStore@TDB_StreamGroup@@UEBA_NAEBVTDB_MatchName@@@Z"]
 fs=sorted((f.struct.BeginAddress,f.struct.EndAddress) for f in p.DIRECTORY_ENTRY_EXCEPTION)
 ix=bisect.bisect_right([f[0] for f in fs],entry)-1
 assert ix>=0 and entry<fs[ix][1]
 begin,end=fs[ix]
 ins=list(Cs(CS_ARCH_X86,CS_MODE_64).disasm(data[p.get_offset_from_rva(entry):p.get_offset_from_rva(end)],base+entry))
 if ins and ins[-1].mnemonic=="int3":ins=[i for i in ins if i.mnemonic!="int3"]
 calls=[]
 for i in ins:
  if i.mnemonic=="call" and i.op_str.startswith("0x"):
   target=int(i.op_str,16)-base
   calls.append(ex.get(target,""))
 assert any("??8TDB_MatchName@@" in x for x in calls),(year,calls)
 assert any("??0TDB_MatchName@@" in x for x in calls),(year,calls)
 assert any(i.mnemonic=="add" and i.op_str=="rbx, 8" for i in ins)
 assert any(i.mnemonic=="cmp" and i.op_str=="rbx, rsi" for i in ins)
 assert any(i.mnemonic=="movzx" and i.op_str=="eax, bl" for i in ins)
 assert any(i.mnemonic=="setne" and i.op_str=="bl" for i in ins)
 # The callee walks a vector of allowed matchnames and performs exact
 # TDB_MatchName comparison; registration alone does not add a whitelist entry.
 out[year]={"sha256":hashlib.sha256(data).hexdigest(),"entry_rva":hex(entry),
 "pdata_end":hex(end),"matchname_copy_equal_calls":calls,
 "observed_8byte_vector_iteration":True,"exact_matchname_comparison":True,
 "custom_child_instantiation_proven":False}
 print("PASS",year,"TDB_StreamGroup::CanStore == whitelist MatchName search",flush=True)
dst=Path(r"D:\Developer\ShapeLayerAE\results\tdb_group_canstore_canonical_whitelist_2025_2026.json")
dst.write_text(json.dumps({"evidence":"E2-L compiled TDB exact allowed-matchname linear scan","versions":out},indent=2)+"\n")
print("SAVED",dst)
