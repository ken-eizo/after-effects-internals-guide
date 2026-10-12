"""Inspect native BEE_DoCommand 32-byte command table in installed 2025/26
BEE.dll. Decode file relocation pointers and find NewVectorLayer handler.
No live host reads/calls; read-only PE data.
"""
from pathlib import Path
import pefile,struct,json,hashlib,bisect
pairs={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0xfec250,0x65cdd0,0x9a),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x104c530,0x6783e0,0x9f)}
out={}
for y,(path,table,shape,n) in pairs.items():
 raw=Path(path).read_bytes();p=pefile.PE(data=raw);base=p.OPTIONAL_HEADER.ImageBase
 ex={e.address:e.name.decode(errors="replace") for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 found=[];entries=[];static_names=[]
 for idx in range(n+1):
  rva=table+32*idx
  try:buf=raw[p.get_offset_from_rva(rva):p.get_offset_from_rva(rva)+32]
  except:continue
  if len(buf)!=32:continue
  q0,q1,q2,q3=struct.unpack("<QQQQ",buf)
  vals=[q0,q1,q2,q3]
  row={"index":idx,"entry_rva":hex(rva),
       "qwords":[hex(k) for k in vals],
       "pointers_rva":[hex(k-base) if base<=k<base+p.OPTIONAL_HEADER.SizeOfImage else "" for k in vals],
       "exports":[ex.get(k-base,"") if base<=k<base+p.OPTIONAL_HEADER.SizeOfImage else "" for k in vals]}
  if any(x==base+shape for x in vals):found.append(row)
  entries.append(row)
 print(y,"base",hex(base),"table",hex(table),"entries",len(entries),
       "NewVectorLayer direct pointer found",len(found),flush=True)
 for f in found: print(f,flush=True)
 for idx in (0,1,2,4,11,30,55,70,100,n-1,n):
  if idx<len(entries):print(idx,entries[idx]["pointers_rva"],entries[idx]["exports"],flush=True)
 out[y]={"image_sha256":hashlib.sha256(raw).hexdigest(),"image_base":hex(base),
     "table_rva":hex(table),"entries":entries,"new_vector_layer_direct_pointers":found}
dst=Path(r"D:\Developer\ShapeLayerAE\results\bee_native_command_table_32byte_entries_2025_2026.json")
dst.write_text(json.dumps({"evidence":"E2-L pinned BEE native command table qword PE-file identities; no runtime calls","versions":out},indent=2)+"\n")
print("SAVED",dst)
