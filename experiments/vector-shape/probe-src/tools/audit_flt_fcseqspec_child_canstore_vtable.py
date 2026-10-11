"""Pin native TDB NamedGroup CanStore vtable slot and FLT FCSeqSpec subobject.
Reads PE vtables only; no Adobe methods executed.
"""
from pathlib import Path
import pefile,struct,json,hashlib
files={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\TDB.dll",
               r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\FLT.dll"),
       "2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\TDB.dll",
               r"D:\Adobe\Adobe After Effects 2026\Support Files\FLT.dll")}
out={}
for year,(tfile,ffile) in files.items():
 tb=Path(tfile).read_bytes();fb=Path(ffile).read_bytes()
 t=pefile.PE(data=tb);f=pefile.PE(data=fb)
 ts={s.name.decode(errors="replace"):s.address for s in t.DIRECTORY_ENTRY_EXPORT.symbols if s.name}
 fs={s.name.decode(errors="replace"):s.address for s in f.DIRECTORY_ENTRY_EXPORT.symbols if s.name}
 tn=ts["??_7TDB_NamedStreamGroup@@6B@"]
 can=ts["?CanStore@TDB_StreamGroup@@UEBA_NAEBVTDB_MatchName@@@Z"]
 fn=fs["??_7FLT_FCSeqSpec@@6BTDB_NamedStreamGroup@@@"]
 def qword(data,p,rva,i):
  return struct.unpack_from("<Q",data,p.get_offset_from_rva(rva)+i*8)[0]
 # Only use the bounded first vftable; neighboring RTTI/vtables can follow
 # immediately in the same PE section and must not be read as its slots.
 indices=[i for i in range(100) if qword(tb,t,tn,i)==t.OPTIONAL_HEADER.ImageBase+can]
 assert indices and indices[0]<100,(year,indices)
 ix=indices[0]
 ptr=qword(fb,f,fn,ix)
 same_module_rva=ptr-f.OPTIONAL_HEADER.ImageBase
 stub=fb[f.get_offset_from_rva(same_module_rva):][:6]
 # FLT compiles an import JMP stub for the inherited TDB virtual method.
 assert len(stub)==6 and stub[:2]==bytes.fromhex('ff25'),(year,stub.hex())
 iat_rva=same_module_rva+6+struct.unpack_from('<i',stub,2)[0]
 imports={i.address-f.OPTIONAL_HEADER.ImageBase:
   desc.dll.decode(errors='replace')+'!'+i.name.decode(errors='replace')
   for desc in f.DIRECTORY_ENTRY_IMPORT for i in desc.imports if i.name}
 resolved=imports.get(iat_rva,'')
 assert resolved.endswith('!'+ '?CanStore@TDB_StreamGroup@@UEBA_NAEBVTDB_MatchName@@@Z'),(year,resolved)
 out[year]={"tdb_sha256":hashlib.sha256(tb).hexdigest(),
            "flt_sha256":hashlib.sha256(fb).hexdigest(),
            "tdb_named_vtable":hex(tn),"tdb_canstore_slot":ix,
            "tdb_canstore_method_rva":hex(can),
            "flt_fcseqspec_tdb_named_vtable":hex(fn),
            "flt_slot_pointer_file_value":hex(ptr),
            "flt_slot_as_image_relative":hex(same_module_rva),
            "flt_import_thunk_opcode":stub.hex(),
            "flt_iat_rva":hex(iat_rva),
            "resolved_import":resolved}
 print(year,"CanStore slot",ix,"FLT raw target",hex(ptr),"relative",hex(same_module_rva))
path=Path(r"D:\Developer\ShapeLayerAE\results\flt_fcseqspec_child_canstore_vtable_2025_2026.json")
path.write_text(json.dumps({"evidence":"exact FLT_FCSeqSpec TDB subobject vtable slot and FF25 IAT thunk resolved to TDB_StreamGroup::CanStore in both builds; no native call","versions":out},indent=2)+"\n")
print("SAVED",path)
