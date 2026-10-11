"""EXP-SHAPE-018: relate path-producing operator functions to VectorArt provenance.
Static PE disassembly; function-by-function call target identity in BEE.dll exports.
"""
from pathlib import Path
import pefile,subprocess,re,bisect,json,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP,X86_OP_IMM
root=Path(r"D:\Developer\After Effects Internals Guide")
maps=json.loads((root/"datasets/ae-vector-evaluator-vtable-slot-map-2025-2026.json").read_text())["versions"]
versions={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
"2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
test=["ADBE Vector Shape - Group","ADBE Vector Shape - Rect","ADBE Vector Shape - Ellipse",
      "ADBE Vector Graphic - Fill","ADBE Vector Filter - Trim","ADBE Vector Filter - Repeater"]
rows={}
rx=re.compile(r"^\s*\d+\s+[0-9a-fA-F]+\s+([0-9a-fA-F]{8})\s+(\S+)")
for ver,path in versions.items():
 p=pefile.PE(path);blob=Path(path).read_bytes();base=p.OPTIONAL_HEADER.ImageBase
 exp={}
 for l in subprocess.run(["dumpbin","/exports",path],capture_output=True,text=True,errors="replace",check=True).stdout.splitlines():
  m=rx.match(l)
  if m:exp[int(m.group(1),16)]=m.group(2)
 imp={t.address:k.dll.decode(errors="replace")+"!"+t.name.decode(errors="replace") for k in p.DIRECTORY_ENTRY_IMPORT for t in k.imports if t.name}
 spans=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION)
 begins=[t[0] for t in spans]
 cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
 selected=[]
 for name in test:
  row=next(x for x in maps[ver]["rows"] if x["matchName"]==name)
  table=next(t for t in row["tables"] if t["subobject_offset"]==0)
  slots=[]
  for sl in table["slots"]:
   if sl["index"] not in (4,5,6,7):continue
   rva=int(sl["func_rva"],16);idx=bisect.bisect_right(begins,rva)-1
   if idx<0 or rva>=spans[idx][1]:continue
   end=spans[idx][1]
   calls=[]
   for inst in cs.disasm(blob[p.get_offset_from_rva(rva):p.get_offset_from_rva(rva)+min(end-rva,13000)],base+rva):
    if inst.mnemonic not in ("call","jmp") or not inst.operands:continue
    o=inst.operands[0];t=None
    if o.type==X86_OP_IMM:t=o.imm
    elif o.type==X86_OP_MEM and o.mem.base==X86_REG_RIP:t=inst.address+inst.size+o.mem.disp
    calls.append({"site":hex(inst.address-base),"target":hex(t-base) if t else None,
                  "symbol":(imp.get(t,"") or exp.get(t-base,"")) if t else "", "instruction":inst.mnemonic+" "+inst.op_str})
   slots.append({"slot":sl["index"],"begin_rva":hex(rva),"end_rva":hex(end),"calls":calls})
  selected.append({"matchName":name,"slots":slots})
 rows[ver]={"SHA256":hashlib.sha256(blob).hexdigest(),"entries":selected}
 print("==",ver,flush=True)
 for x in selected:
  print(x["matchName"],flush=True)
  for sl in x["slots"]:
   print(" SLOT",sl["slot"],sl["begin_rva"],"calls",len(sl["calls"]),flush=True)
   for c in sl["calls"]:
    if "BEE_VectorArt" in c["symbol"] or "OriginInfo" in c["symbol"] or "TDB_Stream" in c["symbol"]:
     print(" ",c["site"],c["symbol"][:175],flush=True)
dest=root/"datasets/ae-vector-operator-vectorart-provenance-calls-2025-2026.json"
dest.write_text(json.dumps({"classification":"E2-L static native geometry operator callsites","versions":rows},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dest,flush=True)
