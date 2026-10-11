"""EXP-SHAPE-024: compare BEE_AVLayer and BEE_VectorLayer real vtables.
Locate the production Rasterize2DGraph virtual function pointer in their
true exported vftables in two installed builds, without running Adobe code.
"""
from pathlib import Path
import pefile,re,json,struct,hashlib,subprocess
base=Path(r"D:\Developer\After Effects Internals Guide")
binaries={"AE2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
          "AE2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")}
pattern=re.compile(r"^\s*\d+\s+[0-9a-fA-F]+\s+([0-9a-fA-F]{8})\s+(\S+)")
selectors={
 "av_vtable":"??_7BEE_AVLayer@@6B@",
 "vector_vtable":"??_7BEE_VectorLayer@@6B@",
 "av_raster":"?Rasterize2DGraph@BEE_AVLayer@@",
 "vector_raster":"?Rasterize2DGraph@BEE_VectorLayer@@",
 "vector_get_art":"?GetVectorArt@BEE_VectorLayer@@",
 "vector_type":"?GetLayerType@BEE_VectorLayer@@",
 "av_type":"?GetLayerType@BEE_AVLayer@@"
}
result={}
for ver,path in binaries.items():
 raw=path.read_bytes(); pe=pefile.PE(data=raw);imagebase=pe.OPTIONAL_HEADER.ImageBase
 exports={}
 for line in subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,
                            text=True,errors="replace",check=True).stdout.splitlines():
  m=pattern.match(line)
  if m:exports[int(m.group(1),16)]=m.group(2)
 picked={}
 for k,v in selectors.items():
  hits=[(addr,name) for addr,name in exports.items() if v in name]
  picked[k]=hits[0][0] if len(hits)==1 else None
  print(ver,k,[(hex(i),n[:93]) for i,n in hits[:3]],flush=True)
 tables={}
 for k in ("av_vtable","vector_vtable"):
  at=picked[k]
  if at is None:continue
  entries=[]
  # exported MSVC vtable symbols address the first function slot (after RTTI ptr).
  for i in range(600):
   slot=at+8*i
   try:va=struct.unpack_from("<Q",raw,pe.get_offset_from_rva(slot))[0]
   except Exception:break
   addr=va-imagebase
   executable=any((sec.Characteristics & 0x20000000)!=0 and
     sec.VirtualAddress<=addr<sec.VirtualAddress+sec.Misc_VirtualSize for sec in pe.sections)
   if not executable:
    if i>=8:break
   entries.append({"slot_index":i,"slot_offset":hex(i*8),
      "target_rva":hex(addr),"is_executable":bool(executable),
      "exported_name":exports.get(addr,"")})
  tables[k]={"rva":hex(at),"entries":entries}
  for target in ("av_raster","vector_raster","vector_type","av_type"):
   addr=picked[target]
   if addr is not None:
    occur=[e for e in entries if int(e["target_rva"],16)==addr]
    if occur:print("VTABLE_MATCH",ver,k,target,"offsets",
                   [(e["slot_index"],e["slot_offset"]) for e in occur],flush=True)
 result[ver]={"source":str(path),"sha256":hashlib.sha256(raw).hexdigest(),
              "rvas":{k:hex(v) if v is not None else None for k,v in picked.items()},
              "vtables":tables}
dest=base/"datasets/ae-native-av-vs-vector-layer-raster-vtable-2025-2026.json"
dest.write_text(json.dumps({"classification":"E2-L. PE export and VFTABLE data entries in pinned DLL binaries; symbolized direct target addresses. No host execution.",
"versions":result},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dest,flush=True)
