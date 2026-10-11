"""Recover native MSVC x64 RTTI inheritance references of
BEE::ae::DynamicStreamEffectsParser in pinned AE2025/26.
All reads are PE files; never load or call Adobe private code.
"""
from pathlib import Path
import struct,json,hashlib
import pefile
BIN={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
     "2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
def refs(data,needle):
 i=0
 while True:
  k=data.find(needle,i)
  if k<0:break
  yield k
  i=k+1

def candidate_chd_xrefs(data,p,arr_index):
 # A base descriptor can occur at any index in the inheritance array,
 # not just the first element. Check each possible array start.
 for skip in range(32):
  off=arr_index-skip*4
  if off<0:break
  try:arr_rva=p.get_rva_from_offset(off)
  except Exception:continue
  for ch in refs(data,struct.pack('<I',arr_rva)):
   if ch<12 or ch+4>len(data):continue
   sig,attr,count,ptr=struct.unpack_from('<4I',data,ch-12)
   if sig<=1 and attr<=255 and 1<=count<=80 and count>skip and ptr==arr_rva:
    yield arr_rva,ch
out={}
for year,file in BIN.items():
 data=Path(file).read_bytes();p=pefile.PE(data=data)
 base=p.OPTIONAL_HEADER.ImageBase
 hit=list(refs(data,b".?AVDynamicStreamEffectsParser@BEE@ae@@\0"))
 assert len(hit)==1,(year,hit)
 tdoff=hit[0]-16;tdrva=p.get_rva_from_offset(tdoff)
 print("YEAR",year,"target TypeDescriptor",hex(tdrva),flush=True)
 derived=[]
 bcd_candidates=[]
 for off in refs(data,struct.pack("<I",tdrva)):
  if off<0x100 or off+28>len(data):continue
  fields=struct.unpack_from("<7I",data,off)
  _,num,mdisp,pdisp,vdisp,attrs,base_chd=fields
  if num>1000 or mdisp>0x20000 or attrs>0xffff:continue
  try:r=p.get_rva_from_offset(off)
  except Exception:continue
  bcd_candidates.append({"rva":r,"fields":fields})
 print("type in candidate base descriptors",len(bcd_candidates),flush=True)
 seen=set()
 for bcd in bcd_candidates:
  bcd_rva=bcd["rva"]
  for arr_index in refs(data,struct.pack("<I",bcd_rva)):
   # BaseClassArray consists of RVA BCDs; find all prospective CHD pointers
   if arr_index%4:continue
   for arr_rva,choff in candidate_chd_xrefs(data,p,arr_index):
    if choff<12:continue
    candidate=choff-12
    if candidate<0 or candidate+16>len(data):continue
    sig,attrib,nbase,back=struct.unpack_from("<4I",data,candidate)
    if sig>1 or attrib>0xff or nbase<1 or nbase>80 or back!=arr_rva:continue
    try:chrva=p.get_rva_from_offset(candidate)
    except Exception:continue
    for colxref in refs(data,struct.pack("<I",chrva)):
     if colxref<16:continue
     coff=colxref-16
     if coff<0 or coff+24>len(data):continue
     sg,offset,cd,ptype,pdesc,self_rva=struct.unpack_from("<6I",data,coff)
     try:colrva=p.get_rva_from_offset(coff)
     except Exception:continue
     if sg!=1 or self_rva!=colrva or pdesc!=chrva or offset>0x20000:continue
     try:
      td_off2=p.get_offset_from_rva(ptype)
      en=data.find(b"\0",td_off2+16,td_off2+320)
      name=data[td_off2+16:en].decode(errors="replace")
     except Exception:continue
     if not name.startswith(".?A"):continue
     for vtloc in refs(data,struct.pack("<Q",base+colrva)):
      vft_off=vtloc+8
      if vft_off+8*23>len(data):continue
      try:vftrva=p.get_rva_from_offset(vft_off)
      except Exception:continue
      key=(name,vftrva,colrva)
      if key in seen:continue
      seen.add(key)
      ptr=struct.unpack_from("<Q",data,vft_off+0xb0)[0]
      derived.append({"type":name,"vtable_rva":hex(vftrva),
                      "complete_object_locator":hex(colrva),
                      "rtti_offset":offset,"virtual_slot22_target_rva":hex(ptr-base),
                      "base_array_candidate_rva":hex(arr_rva)})
 print("DYNAMIC PARSER RTTI DESCENDANT VTABLES",len(derived),flush=True)
 for row in derived:print(" ",row,flush=True)
 out[year]={"sha256":hashlib.sha256(data).hexdigest(),
            "base_TypeDescriptor_rva":hex(tdrva),
            "candidate_base_descriptors":len(bcd_candidates),
            "validated_rtti_vtables":derived}
dest=Path(r"D:\Developer\ShapeLayerAE\results\bee_dynamic_parser_derived_RTTI_vtable_scan_2025_2026.json")
dest.write_text(json.dumps({"classification":"E2-L heuristic verified MSVC RTTI references; no host invocation; partial inheritance handling","years":out},indent=2)+"\n")
print("SAVED",dest)
