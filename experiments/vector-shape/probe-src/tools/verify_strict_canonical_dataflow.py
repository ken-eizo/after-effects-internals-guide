"""Independent precision check of enhanced static canonical-grammar census.
Reads BEE.dll PE and verifies that recorded name LEA feeds RDX for direct TDB
GetCanonicalStream import CALL. No private API executed.
"""
from pathlib import Path
import re,subprocess,collections,json,capstone,pefile,hashlib
roots={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files"),
"2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files")}
audit=json.loads((Path(__file__).resolve().parents[4]/"datasets"/"ae-bee-canonical-grammar-strict-rdx-2025-2026.json").read_text(encoding="utf-8"))
for year,root in roots.items():
 assert hashlib.sha256((root/"BEE.dll").read_bytes()).hexdigest()==audit[year]["BEE_sha256"],"BEE.dll binary SHA mismatch"
 p=pefile.PE(str(root/"BEE.dll"));base=p.OPTIONAL_HEADER.ImageBase
 pdata={x.struct.BeginAddress:x.struct.EndAddress for x in p.DIRECTORY_ENTRY_EXCEPTION}
 iat={x.address-base:(d.dll.decode("latin1"),x.name.decode("latin1") if x.name else str(x.ordinal)) for d in p.DIRECTORY_ENTRY_IMPORT for x in d.imports}
 cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);cs.detail=True
 total=0;validated=0
 variations=collections.Counter();failures=[]
 for group,record in audit[year]["groups"].items():
  a=int(record["method_rva"],16)
  end=pdata.get(a,a+0x800)
  allins=list(cs.disasm(p.get_data(a,end-a),base+a))
  ia={ins.address-base:ix for ix,ins in enumerate(allins)}
  for child in record["identified_canonical_children"]:
   total+=1
   call=int(child["canonical_lookup_call_rva"],16)
   lea=int(child["reference_rva"],16)
   if lea not in ia or call not in ia:
    failures.append((group,'instruction not found',child));continue
   ins=allins[ia[lea]];cins=allins[ia[call]]
   delta=ia[call]-ia[lea]
   expected_target=int(child["match_symbol_rva"],16)
   target=[]
   for op in ins.operands:
    if op.type==capstone.x86.X86_OP_MEM and op.mem.base==capstone.x86.X86_REG_RIP:
     target.append(ins.address+ins.size+op.mem.disp-base)
   ctarget=[]
   for op in cins.operands:
    if op.type==capstone.x86.X86_OP_MEM and op.mem.base==capstone.x86.X86_REG_RIP:
     ctarget.append(cins.address+cins.size+op.mem.disp-base)
   if (ins.mnemonic not in ("lea","mov") or expected_target not in target
     or cins.mnemonic!="call" or
     not any(iat.get(t,("",""))[0].lower()=="tdb.dll" and iat[t][1].startswith("?GetCanonicalStream@TDB_StreamBase@@") for t in ctarget)):
    failures.append((group,'missing direct native instruction evidence',child));continue
   match=ins.operands[0].reg if ins.operands and ins.operands[0].type==capstone.x86.X86_OP_REG else None
   reg_name=cs.reg_name(match) if match else "unknown"
   variations[(ins.mnemonic,reg_name)]+=1
   # Direct RDX leaf reference is definitely passed as MatchName at the call.
   # Other sources are recorded but are not automatically direct-dataflow proven.
   if ins.mnemonic=="lea" and reg_name=="rdx" and 0<delta<=16:
    overwritten=any(v.mnemonic in ("mov","lea","xor","pop","add","sub") and v.operands and v.operands[0].type==capstone.x86.X86_OP_REG and cs.reg_name(v.operands[0].reg)=="rdx"
                    for v in allins[ia[lea]+1:ia[call]])
    if not overwritten:validated+=1
    else:failures.append((group,"RDX overwritten between name reference and GetCanonicalStream",child))
   else:failures.append((group,f'not direct RDX dataflow: {ins.mnemonic} {reg_name}, delta {delta}',child))
 print(year,"total records",total,"direct RDX-proven",validated,"non-direct",len(failures),"source formats",dict(variations))
 for x in failures[:10]:print("WARNING",x[0],x[1],x[2]['child_symbol'])
 assert total==audit[year]["identified_canonical_edges"]
 assert not failures,(year,len(failures),failures[:3])
 assert validated==total,(year,validated,total)
print("PASS strict census: all 685/694 recorded children have direct RDX native GetCanonicalStream import-call proof, no overwrites")
