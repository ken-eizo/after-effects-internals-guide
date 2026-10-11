"""Decode actual image-relative 8-way native BEE Layer factory jump tables.
No host invocation. Proof of case-to-concrete-constructor switch mapping.
"""
from pathlib import Path
import json,struct,pefile,hashlib
spec={
"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x2e4108),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x2ecfe8)}
dataset=json.loads(Path(r"D:\Developer\ShapeLayerAE\results\native_layer_factory_type_dispatch_2025_2026.json").read_text())["versions"]
report={}
for year,(filename,table_rva) in spec.items():
 data=Path(filename).read_bytes();p=pefile.PE(data=data)
 assert hashlib.sha256(data).hexdigest()==dataset[year]["BEE_sha256"]
 ops=dataset[year]["instructions"]
 off=p.get_offset_from_rva(table_rva)
 table=struct.unpack_from("<8I",data,off)
 rows=[]
 for kind,target in enumerate(table):
  label=next((o["export"].split("@@")[0].removeprefix("??0") for o in ops
               if o["rva"]==hex(target) and o["export"].startswith("??0BEE_")),"")
  # The table jumps to allocator/setup block, not directly to constructor.
  region=[x for x in ops if target<=int(x["rva"],16)<min(target+0x70,0x2e4128 if year=="2025" else 0x2ed008)]
  ctor=[x["export"].split("@@")[0].removeprefix("??0") for x in region
        if x["export"].startswith("??0BEE_") and "Layer@@" in x["export"]]
  row={"layer_type_integer":kind,"branch_rva":hex(target),"constructor_family":ctor,
       "first_operations":[x["m"]+" "+x["args"] for x in region[:6]]}
  rows.append(row)
  print(year,kind,hex(target),ctor,flush=True)
 report[year]={"sha256":dataset[year]["BEE_sha256"],"jump_table_rva":hex(table_rva),"cases":rows}
out=Path(r"D:\Developer\ShapeLayerAE\results\native_layer_factory_jump_table_case_mapping.json")
out.write_text(json.dumps({"classification":"E2-L 8-entry native factory jump table mapping; no host calls",
 "versions":report},indent=2)+"\n",encoding="utf8")
print("SAVED",out)
