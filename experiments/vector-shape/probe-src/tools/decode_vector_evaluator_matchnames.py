"""Reconstruct literal MatchName strings for 20 BEE VectorArt evaluator registrations.
Static PE data, code reference and TDB_MatchName initializer site; no runtime calls.
"""
from pathlib import Path
import pefile,json,re,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP
ROOT=Path(r"D:\Developer\After Effects Internals Guide")
record=json.loads((ROOT/"datasets/ae-native-vector-evaluator-registration-records-2025-2026.json").read_text())
result={}
for ver,path in [("2025",r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
("2026",r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")]:
 p=pefile.PE(path);raw=Path(path).read_bytes();base=p.OPTIONAL_HEADER.ImageBase
 refs=json.loads((ROOT/("datasets/ae-vector-evaluator-matchname-xrefs-"+ver+".json")).read_text())["references"]
 bykey={r["matchname"]["static_matchname_object_rva"]:r for r in record["versions"][ver]["records"]}
 cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
 rows=[]
 for key,row in bykey.items():
  init=[int(x["instruction_rva"],16) for x in refs.get(key,[]) if
        int(x["instruction_rva"],16)<0x30000 and x["op"].startswith("lea rcx,")]
  if not init:
   rows.append({"matchname_global_rva":key,"error":"missing static initializer reference"});continue
  init_rva=min(init)
  buf=raw[p.get_offset_from_rva(init_rva-7):p.get_offset_from_rva(init_rva-7)+7]
  ins=list(cs.disasm(buf,base+init_rva-7))
  litaddr=None
  if len(ins)==1 and ins[0].mnemonic=="lea" and len(ins[0].operands)==2:
   obj=ins[0].operands[1]
   if obj.type==X86_OP_MEM and obj.mem.base==X86_REG_RIP:
    litaddr=ins[0].address+ins[0].size+obj.mem.disp-base
  literal=""
  if litaddr:
   try:
    b=raw[p.get_offset_from_rva(litaddr):p.get_offset_from_rva(litaddr)+160]
    literal=b.split(b"\x00",1)[0].decode("ascii","replace")
   except Exception as ex:literal=repr(ex)
  rows.append({"registration_call_rva":row["registrar_call_rva"],
                "matchname_global_rva":key,"matchname_init_rva":hex(init_rva),
                "ascii_constant_rva":hex(litaddr) if litaddr is not None else None,"name":literal})
 result[ver]={"BEE_sha256":hashlib.sha256(raw).hexdigest(),"records":rows}
 print("====",ver,"count",len(rows),flush=True)
 for r in rows:print(r["registration_call_rva"],r["matchname_global_rva"],repr(r.get("name")),flush=True)
dest=ROOT/"datasets"/"ae-vector-evaluator-matchname-identities-2025-2026.json"
dest.write_text(json.dumps({"evidence":"E2-L native static literal linkage; names recovered at constructor sites, never runtime private calls","versions":result},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dest)
