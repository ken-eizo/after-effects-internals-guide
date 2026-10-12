"""Recover the genuine three-level BEE native Shape Contents canonical UI
schema by disassembling exported FillInCanonicalUILayout methods of:
BEE_VectorLayer / VectorStreamGroup / VectorsStreamGroup (both pinned builds).
No host code is loaded or executed.
"""
from pathlib import Path
import pefile,json,hashlib,bisect
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP
root=Path(r"D:\Developer\ShapeLayerAE\results")
doc=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-vector-evaluator-matchname-identities-2025-2026.json")
evals=json.loads(doc.read_text())["versions"]
configs={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
"2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
classes=[
"?FillInCanonicalUILayout@BEE_VectorLayer@@",
"?FillInCanonicalUILayout@VectorStreamGroup@BEE_VectorStream@@",
"?FillInCanonicalUILayout@VectorsStreamGroup@BEE_VectorStream@@"]
out={}
for year,file in configs.items():
 raw=Path(file).read_bytes();pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase
 exports={x.name.decode(errors="replace"):x.address for x in pe.DIRECTORY_ENTRY_EXPORT.symbols if x.name}
 imp={i.address:d.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace")
  for d in pe.DIRECTORY_ENTRY_IMPORT for i in d.imports if i.name}
 pdata=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in pe.DIRECTORY_ENTRY_EXCEPTION)
 starts=[a for a,b in pdata]
 known={int(x["matchname_global_rva"],16):x["name"] for x in evals[year]["records"]}
 md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
 functions=[]
 for pattern in classes:
  choices=[(n,a) for n,a in exports.items() if n.startswith(pattern)]
  assert len(choices)==1,(year,pattern,choices)
  symbol,rva=choices[0]
  k=bisect.bisect_right(starts,rva)-1
  assert k>=0 and rva<pdata[k][1]
  first,last=pdata[k]
  ins=list(md.disasm(raw[pe.get_offset_from_rva(first):pe.get_offset_from_rva(last)],base+first))
  ops=[];allcalls=[];matchrefs=[]
  for j,x in enumerate(ins):
   if x.mnemonic!="call" or not x.operands:continue
   arg=x.operands[0]
   if arg.type!=X86_OP_MEM or arg.mem.base!=X86_REG_RIP:continue
   link=imp.get(x.address+x.size+arg.mem.disp,"")
   allcalls.append({"rva":hex(x.address-base),"target":link})
   if "?GetCanonicalStream@TDB_StreamBase@@" not in link:continue
   ref=[]
   for before in ins[max(0,j-16):j]:
    if before.mnemonic!="lea" or len(before.operands)<2:continue
    mem=before.operands[1]
    if mem.type==X86_OP_MEM and mem.mem.base==X86_REG_RIP:
     rv=before.address+before.size+mem.mem.disp-base
     ref.append({"reg":before.reg_name(before.operands[0].reg),
       "matchname_rva":hex(rv),"known_operator":known.get(rv),"site":hex(before.address-base)})
   # Determine nearest previous lea rdx, the canonical matchname argument
   rdx=[r for r in ref if r["reg"]=="rdx"]
   ops.append({"callsite":hex(x.address-base),"last_matchname_arg":rdx[-1] if rdx else None})
  info={"symbol":symbol,"entry_rva":hex(rva),"code_range":[hex(first),hex(last)],
        "canonical_child_lookup_count":len(ops),"canonical_children":ops,
        "import_calls":allcalls}
  functions.append(info)
  print(year,pattern.split("@")[1],"CANONICAL",len(ops),"native bytes",last-first,flush=True)
  for v in ops:print("    ",v["callsite"],v["last_matchname_arg"],flush=True)
 out[year]={"BEE_SHA256":hashlib.sha256(raw).hexdigest(),"three_schema_classes":functions}
dest=root/"bee_vector_native_layer_contents_allowed_children_2025_2026.json"
dest.write_text(json.dumps({"evidence":"E2-L exact 2025/2026 BEE PE exported FillInCanonicalUILayout x64 code, native TDB imported canonical stream links, static only","versions":out},indent=2)+"\n")
print("SAVED",dest)
