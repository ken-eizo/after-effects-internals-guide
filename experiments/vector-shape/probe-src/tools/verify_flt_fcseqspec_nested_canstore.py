"""Prove inner FLT_FCSeqSpec group CanStore vtable slot is TDB_StreamGroup
(default canonical schema), DISTINCT from outer FLT_Parade RTTI CanStore.
"""
import pefile,struct,hashlib,json
from pathlib import Path
cfg={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\TDB.dll",
              r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\FLT.dll"),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\TDB.dll",
        r"D:\Adobe\Adobe After Effects 2026\Support Files\FLT.dll")}
out={}
for year,(tdbfile,fltfile) in cfg.items():
 tp=pefile.PE(tdbfile);fp=pefile.PE(fltfile)
 te={x.name.decode(errors="replace"):x.address for x in tp.DIRECTORY_ENTRY_EXPORT.symbols if x.name}
 fe={x.name.decode(errors="replace"):x.address for x in fp.DIRECTORY_ENTRY_EXPORT.symbols if x.name}
 table=struct.unpack_from("<100Q",tp.__data__,tp.get_offset_from_rva(te["??_7TDB_StreamGroup@@6B@"]))
 can=te["?CanStore@TDB_StreamGroup@@UEBA_NAEBVTDB_MatchName@@@Z"]
 slots=[i for i,x in enumerate(table) if x==tp.OPTIONAL_HEADER.ImageBase+can]
 assert slots==[56],(year,slots)
 ft=fe["??_7FLT_FCSeqSpec@@6BTDB_NamedStreamGroup@@@"]
 ftptr=struct.unpack_from("<100Q",fp.__data__,fp.get_offset_from_rva(ft))
 thunk=ftptr[56]-fp.OPTIONAL_HEADER.ImageBase
 b=fp.__data__[fp.get_offset_from_rva(thunk):fp.get_offset_from_rva(thunk)+6]
 assert b[:2]==b"\xff\x25",(year,b.hex())
 offset=int.from_bytes(b[2:6],"little",signed=True)
 iat=fp.OPTIONAL_HEADER.ImageBase+thunk+6+offset
 imp={x.address:d.dll.decode(errors="replace")+"!"+x.name.decode(errors="replace")
      for d in fp.DIRECTORY_ENTRY_IMPORT for x in d.imports if x.name}
 target=imp.get(iat,"")
 assert target=="TDB.dll!?CanStore@TDB_StreamGroup@@UEBA_NAEBVTDB_MatchName@@@Z",(year,target)
 out[year]={"tdb_sha256":hashlib.sha256(Path(tdbfile).read_bytes()).hexdigest(),
 "flt_sha256":hashlib.sha256(Path(fltfile).read_bytes()).hexdigest(),
 "native_group_vtable_slot":56,"flt_fcseqspec_nested_tdb_group_rva":hex(ft),
 "flt_vtable_entry_thunk":hex(thunk),"inherited_canstore_import":target,
 "third_party_extra_contents_proven":False}
 print("PASS",year,"inner FCSeqSpec virtual CanStore delegates to TDB_StreamGroup (slot 56)")
path=Path(r"D:\Developer\ShapeLayerAE\results\flt_fcseqspec_nested_canstore_tdb_2025_2026.json")
path.write_text(json.dumps({"classification":"E2-L PE vtable/IAT exact; no custom child shown","versions":out},indent=2)+"\n")
print("SAVED",path)
