"""EXP-SHAPE-017 MSVC x64 RTTI class-hierarchy reconstruction for 20 native operators.
No private host execution: static PE .rdata parsing of Complete Object Locators,
Class Hierarchy Descriptors and Base Class Descriptors. Validate bounds and signatures.
"""
from pathlib import Path
import pefile,json,struct,hashlib
root=Path(r"D:\Developer\After Effects Internals Guide")
source=json.loads((root/"datasets/ae-vector-evaluator-vtable-slot-map-2025-2026.json").read_text())["versions"]
paths={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),"2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")}
res={}
for ver,path in paths.items():
 pe=pefile.PE(path);base=pe.OPTIONAL_HEADER.ImageBase
 image=pe.get_memory_mapped_image()
 def u32(rva):return struct.unpack_from("<I",image,rva)[0]
 def i32(rva):return struct.unpack_from("<i",image,rva)[0]
 def u64(rva):return struct.unpack_from("<Q",image,rva)[0]
 def inrange(rva,n):return 0<=rva<=len(image)-n
 def textname(rva):
  if not inrange(rva,22):return "<out-of-range>"
  return image[rva+16:rva+260].split(b"\0",1)[0].decode("ascii","replace")
 entries=[]
 for row in source[ver]["rows"]:
  tables=[]
  for t in row["tables"]:
   vrva=int(t["rva"],16)
   if not inrange(vrva-8,8):continue
   col=u64(vrva-8)-base
   if not inrange(col,24) or u32(col)!=1:continue
   offs=u32(col+4);type_rva=u32(col+12);chd=u32(col+16);self_rva=u32(col+20)
   if not inrange(chd,16):continue
   nbase=u32(chd+8);basearr=u32(chd+12)
   chain=[]
   if nbase>32 or not inrange(basearr,nbase*4):continue
   for i in range(nbase):
    desc=u32(basearr+4*i)
    if not inrange(desc,28):continue
    typ=u32(desc)
    contained=u32(desc+4)
    mdisp=i32(desc+8);pdisp=i32(desc+12);vdisp=i32(desc+16)
    attrs=u32(desc+20)
    chain.append({"class":textname(typ),"mdisp":mdisp,"pdisp":pdisp,"vdisp":vdisp,
                  "contained":contained,"attributes":hex(attrs)})
   tables.append({"subobject_offset":offs,"vtable_rva":hex(vrva),"complete_object_locator_rva":hex(col),
                  "class_name":textname(type_rva),"rtti_hierarchy":{"attrs":hex(u32(chd+4)),"base_count":nbase,"bases":chain},
                  "self_rva_matches":self_rva==col})
  entries.append({"matchName":row["matchName"],"tables":tables})
 res[ver]={"file_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"rows":entries}
 print("==",ver,"entries",len(entries),flush=True)
 for row in entries:
  v=next((t for t in row["tables"] if t["subobject_offset"]==0),None)
  if not v:continue
  b=[(x["class"].split("@")[0],x["mdisp"],x["pdisp"]) for x in v["rtti_hierarchy"]["bases"]]
  print(row["matchName"],"N",len(b),b,flush=True)
dest=root/"datasets/ae-native-vector-operator-rtti-inheritance-2025-2026.json"
dest.write_text(json.dumps({"classification":"E2-L, MSVC x64 static RTTI hierarchy; private ABI, no runtime interaction","versions":res},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dest)
