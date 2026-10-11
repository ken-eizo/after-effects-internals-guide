"""EXP-SHAPE-015: map exact evaluator vtable slots, RTTI subobjects and code ownership.
Static read-only disassembly of locally installed binaries; no Adobe functions called.
"""
from pathlib import Path
import json,pefile,re,subprocess,bisect,hashlib,struct
ROOT=Path(r"D:\Developer\After Effects Internals Guide")
names=json.loads((ROOT/"datasets/ae-vector-evaluator-matchname-identities-2025-2026.json").read_text())["versions"]
vts=json.loads((ROOT/"datasets/ae-native-vector-evaluator-vtable-rtti-2025-2026.json").read_text())["versions"]
binary={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
        "2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")}
rx=re.compile(r"^\s*\d+\s+[0-9a-fA-F]+\s+([0-9a-fA-F]{8})\s+(\S+)")
out={}
for ver,loc in binary.items():
 p=pefile.PE(loc);base=p.OPTIONAL_HEADER.ImageBase
 img=p.get_memory_mapped_image()
 syms={}
 for line in subprocess.run(["dumpbin","/exports",str(loc)],capture_output=True,text=True,errors="replace",check=True).stdout.splitlines():
  m=rx.match(line)
  if m:syms[int(m.group(1),16)]=m.group(2)
 functions=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION)
 starts=[x[0] for x in functions]
 rows=[]
 for key,row in zip(names[ver]["records"],vts[ver]["records"]):
  all_classes=row["matched_evaluator_classes"]
  candidates=[x for x in all_classes if x["class_rtti"].split("@")[0].startswith(".?AV") and
              not any(t in x["class_rtti"] for t in ("OperatorT@", "FilterOperator@", "RefCountedInterface@"))]
  # Take last concrete class for each exact registration block; two vtables often exist for one class.
  cname=candidates[-1]["class_rtti"] if candidates else all_classes[-1]["class_rtti"]
  types=[x for x in all_classes if x["class_rtti"]==cname]
  tables=[]
  for t in types:
   rva=int(t["vtable_rva"],16)
   slots=[]
   for j in range(12):
    try:
     ptr=struct.unpack_from("<Q",img,rva+j*8)[0]
     fn_rva=ptr-base
     in_exec=any(s.VirtualAddress<=fn_rva<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData)
                 and bool(s.Characteristics&0x20000000) for s in p.sections)
     if not in_exec:break
     idx=bisect.bisect_right(starts,fn_rva)-1
     b=starts[idx] if idx>=0 and fn_rva<functions[idx][1] else None
     slots.append({"index":j,"vtable_byte_offset":hex(j*8),"func_rva":hex(fn_rva),"exact_export_name":syms.get(fn_rva,""),
                    "entry_function_start":hex(b) if b is not None else None,
                    "starts_at_function_boundary":bool(b==fn_rva)})
    except (struct.error,OverflowError):break
   tables.append({"rva":t["vtable_rva"],"subobject_offset":t["secondary_vtable_offset"],"slots":slots})
  rows.append({"matchName":key["name"],"concrete_rtti":cname,"call":key["registration_call_rva"],"tables":tables})
 out[ver]={"sha256":hashlib.sha256(loc.read_bytes()).hexdigest(),"rows":rows}
 print("====",ver,"entries",len(rows),flush=True)
 for row in rows:
  print(row["matchName"],row["concrete_rtti"].split("@")[0],flush=True)
  for table in row["tables"]:
   vals=[(s["index"],s["func_rva"],s["exact_export_name"].split("@")[0]) for s in table["slots"]]
   print("  subobject",table["subobject_offset"],"vftable",table["rva"],vals,flush=True)
dst=ROOT/"datasets"/"ae-vector-evaluator-vtable-slot-map-2025-2026.json"
dst.write_text(json.dumps({"classification":"E2-L: exact static .rdata vtable code pointers and MSVC RTTI, no plugin ABI guarantee","versions":out},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dst,flush=True)
