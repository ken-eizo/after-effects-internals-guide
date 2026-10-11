"""Inspect which TDB.dll factory registration methods BEE imports.
Only PE symbol imports, no runtime calls.
"""
from pathlib import Path
import pefile,json
for version,path in [("2025",r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),("2026",r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")]:
    pe=pefile.PE(path,fast_load=True);pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]])
    for lib in getattr(pe,"DIRECTORY_ENTRY_IMPORT",[]):
        if lib.dll.lower()!=b"tdb.dll":continue
        names=[a.name.decode(errors="replace") for a in lib.imports if a.name]
        terms=("RegisterFactoryFunc","UnregisterFactoryFunc","RegisterCanonicalInstance","GetCanonicalInstance","CreateStream@TDB_StreamFactory",
               "GetFactory@TDB_StreamBase","GetFactory@TDB_Project","RegisterStreams","TDB_StreamFactory")
        print("==",version,"TDB imports",len(names))
        for n in names:
            if any(t in n for t in terms):print(n[:330])
