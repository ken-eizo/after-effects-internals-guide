"""Locate static code references to 20 BEE evaluator MatchName global objects.
No runtime access, static instruction decoding only.
"""
from pathlib import Path
import pefile,re,json,collections
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
ROOT=Path(r"D:\Developer\After Effects Internals Guide")
src=json.loads((ROOT/"datasets/ae-native-vector-evaluator-registration-records-2025-2026.json").read_text())
for ver,path in [("2025",r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
("2026",r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")]:
 p=pefile.PE(path,fast_load=True);base=p.OPTIONAL_HEADER.ImageBase
 keys={int(row["matchname"]["static_matchname_object_rva"],16) for row in src["versions"][ver]["records"]}
 patterns=re.compile(r"\[rip\s*([+-])\s*0x([0-9a-fA-F]+)\]")
 hits=collections.defaultdict(list)
 md=Cs(CS_ARCH_X86,CS_MODE_64);md.skipdata=True
 for sec in p.sections:
  if not sec.Characteristics&0x20000000:continue
  for addr,size,op,arg in md.disasm_lite(sec.get_data(),base+sec.VirtualAddress):
   if "rip" not in arg:continue
   m=patterns.search(arg)
   if not m:continue
   delta=int(m.group(2),16)*(1 if m.group(1)=="+" else -1)
   target=addr+size+delta-base
   if target in keys:
    hits[hex(target)].append({"instruction_rva":hex(addr-base),"op":op+" "+arg})
 print("==",ver,"keys",len(keys),"ref_count",sum(len(v) for v in hits.values()),flush=True)
 for key,v in hits.items():print(" ",key,[(x["instruction_rva"],x["op"][:85]) for x in v[:12]],flush=True)
 outfile=ROOT/"datasets"/("ae-vector-evaluator-matchname-xrefs-"+ver+".json")
 outfile.write_text(json.dumps({"evidence":"E2-L direct RIP refs to static MatchName globals, not initialized values","version":ver,
                              "references":dict(hits)},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
