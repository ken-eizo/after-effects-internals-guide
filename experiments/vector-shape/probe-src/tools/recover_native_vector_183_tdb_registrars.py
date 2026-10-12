"""Resolve all four phases of BEE_VectorLayer private TDB Schema init:
55 + 47 + 19 + 62 creator registration sites (both builds).
Crossmatch native MatchName global identities to 20 BEE vector operators.
Offline PE code only; no AE plugin installation or private runtime calls.
"""
from pathlib import Path
import pefile,json,hashlib,bisect
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP
cfg={
"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
 [("base_properties",0x715e80,55),("vector_properties",0x716890,47),("vector_operators",0x717140,19)]),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",
 [("base_properties",0x738360,55),("vector_properties",0x738d50,47),("vector_operators",0x7395e0,19)])
}
base=Path(r"D:\Developer\ShapeLayerAE\results")
src=json.loads((base/"bee_vector_layer_62_native_tdb_creators_2025_2026.json").read_text())["versions"]
op=json.loads(Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-vector-evaluator-matchname-identities-2025-2026.json").read_text())["versions"]
out={}
for year,(path,routines) in cfg.items():
 raw=Path(path).read_bytes();p=pefile.PE(data=raw);imagebase=p.OPTIONAL_HEADER.ImageBase
 ranges=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION)
 starts=[x[0] for x in ranges]
 imported={x.address:desc.dll.decode(errors="replace")+"!"+x.name.decode(errors="replace") for desc in p.DIRECTORY_ENTRY_IMPORT for x in desc.imports if x.name}
 exports={x.address:x.name.decode(errors="replace") for x in p.DIRECTORY_ENTRY_EXPORT.symbols if x.name}
 decoder=Cs(CS_ARCH_X86,CS_MODE_64);decoder.detail=True
 blocks=[]
 for name,entry,expect in routines:
  i=bisect.bisect_right(starts,entry)-1
  assert i>=0 and entry<ranges[i][1]
  begin,end=ranges[i]
  instructions=list(decoder.disasm(raw[p.get_offset_from_rva(begin):p.get_offset_from_rva(end)],imagebase+begin))
  hits=[]
  for j,x in enumerate(instructions):
   if x.mnemonic!="call" or not x.operands or x.operands[0].type!=X86_OP_MEM or x.operands[0].mem.base!=X86_REG_RIP:continue
   target=x.address+x.size+x.operands[0].mem.disp
   if "?Register@TDB_ScRegisterStreams@@" not in imported.get(target,""):continue
   near=[]
   for y in instructions[max(0,j-21):j]:
    if y.mnemonic=="lea" and len(y.operands)==2 and y.operands[1].type==X86_OP_MEM and y.operands[1].mem.base==X86_REG_RIP:
     rv=y.address+y.size+y.operands[1].mem.disp-imagebase
     near.append({"arg":y.reg_name(y.operands[0].reg),"rva":hex(rv),
                   "export":exports.get(rv,"")})
   possible=[x for x in near if x["arg"]=="rdx"]
   hits.append({"site":hex(x.address-imagebase),
                "matchname":possible[-1] if possible else None})
  assert len(hits)==expect,(year,name,len(hits),expect)
  blocks.append({"name":name,"function_entry":hex(entry),"register_call_count":len(hits),
                 "registrations":hits})
  print(year,name,len(hits),"MatchName immediate pointers",sum(h["matchname"] is not None for h in hits),flush=True)
 main=src[year]["entries"]
 assert len(main)==62
 known={int(x["matchname_global_rva"],16):x["name"] for x in op[year]["records"]}
 joined={}
 for b in blocks:
  for row in b["registrations"]:
   if row["matchname"]:
    k=int(row["matchname"]["rva"],16)
    if k in known:
     joined.setdefault(known[k],[]).append({"block":b["name"],"site":row["site"]})
 for row in main:
  k=int(row["match"]["data_rva"],16)
  if k in known:
   joined.setdefault(known[k],[]).append({"block":"vector_layer_main","site":row["call_rva"]})
 print(year,"operator MatchName globals directly registered in four-phase TDB schema",len(joined),"/20",flush=True)
 for name in sorted(joined):print(" ",name,joined[name],flush=True)
 out[year]={"BEE_SHA256":hashlib.sha256(raw).hexdigest(),
 "stages":blocks,
 "vector_layer_main_registration_count":len(main),
 "total_static_registration_calls":sum(x["register_call_count"] for x in blocks)+len(main),
 "operator_matchnames_joined_to_native_TDB_creator_registration":joined}
dst=base/"bee_native_vector_all183_tdb_registration_pipeline_2025_2026.json"
dst.write_text(json.dumps({"evidence":"E2-L exact AE2025/26 Shape native initializer; 55+47+19+62 potential registration sites; conditional runtime branches not assumed", "versions":out},indent=2)+"\n")
print("SAVED",dst)
