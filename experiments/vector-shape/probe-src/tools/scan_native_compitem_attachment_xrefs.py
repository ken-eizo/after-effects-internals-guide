"""Find independent native incoming paths to real BEE_CompItem::AttachLayerToCompOnly.
Read-only static relative-call xrefs in exact pinned AE2025/26 BEE.dll.
"""
from pathlib import Path
import bisect,json,pefile,struct,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
cfg={
 "2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",[0x392120,0x3920f0]),
 "2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",[0x39d4d0,0x39d4a0])}
out={}
for year,(path,targets) in cfg.items():
 raw=Path(path).read_bytes()
 p=pefile.PE(data=raw,fast_load=True)
 p.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXCEPTION"],
    pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXPORT"]])
 funcs=sorted((int(e.struct.BeginAddress),int(e.struct.EndAddress)) for e in p.DIRECTORY_ENTRY_EXCEPTION)
 begins=[lo for lo,hi in funcs]
 exps=sorted((int(x.address),x.name.decode(errors="replace")) for x in p.DIRECTORY_ENTRY_EXPORT.symbols if x.name)
 expStarts=[x[0] for x in exps]
 dis=Cs(CS_ARCH_X86,CS_MODE_64)
 def locate(rv):
  idx=bisect.bisect_right(begins,rv)-1
  if idx<0 or rv>=funcs[idx][1]:return None
  return funcs[idx]
 def nearname(rv):
  k=bisect.bisect_right(expStarts,rv)-1
  if k<0:return ""
  return exps[k][1] if exps[k][0]==rv else ""
 references=[]
 for s in p.sections:
  if not s.Characteristics & 0x20000000:continue
  sect=raw[s.PointerToRawData:s.PointerToRawData+s.SizeOfRawData]
  for i in range(len(sect)-5):
   if sect[i] not in (0xE8,0xE9):continue
   callsite=s.VirtualAddress+i
   target=callsite+5+struct.unpack_from("<i",sect,i+1)[0]
   if target not in targets:continue
   bounds=locate(callsite)
   if not bounds:continue
   # Disassemble at least 5 bytes: exact instruction at scanned site.
   pos=p.get_offset_from_rva(callsite)
   nextins=next(dis.disasm(raw[pos:pos+16],p.OPTIONAL_HEADER.ImageBase+callsite),None)
   if not nextins or nextins.mnemonic not in ("call","jmp") or nextins.address!=p.OPTIONAL_HEADER.ImageBase+callsite:continue
   if int(nextins.op_str,16)-p.OPTIONAL_HEADER.ImageBase!=target:continue
   references.append({"caller_begin_rva":hex(bounds[0]),"caller_end_rva":hex(bounds[1]),
     "caller_export":nearname(bounds[0]),"callsite_rva":hex(callsite),"type":nextins.mnemonic,
     "callee_rva":hex(target)})
 refs=sorted(references,key=lambda r:int(r["callsite_rva"],16))
 out[year]={"BEE_SHA256":hashlib.sha256(raw).hexdigest(),"callee_rvas":[hex(n) for n in targets],
   "inbound_direct_xrefs":refs,"inbound_direct_xref_count":len(refs),
   "conclusion":"static inbound direct call routes; indirect and dynamic virtual calls are not listed"}
 print("VERSION",year,"INCOMING",len(refs),flush=True)
 for x in refs[:80]:print(x,flush=True)
dst=Path(r"D:\Developer\ShapeLayerAE\results\bee_native_compitem_attach_inbound_xrefs_2025_2026.json")
dst.write_text(json.dumps({"evidence":"E2-L binary x64 exact direct calls only","versions":out},indent=2)+"\n")
print("SAVED",dst)
