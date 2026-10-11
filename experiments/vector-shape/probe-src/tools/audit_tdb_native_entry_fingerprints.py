"""Read-only audit of five TDB private export instruction-entry fingerprints.
Does not load Adobe DLLs into a process or call private APIs.
"""
import hashlib
from pathlib import Path
import pefile

targets = {
    2025: Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\TDB.dll"),
    2026: Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\TDB.dll"),
}
names = {
 "getter": "?Get_AE_StreamFactory@@YAPEAVTDB_StreamFactory@@XZ",
 "matchname_ctor": "??0TDB_MatchName@@QEAA@PEBD_N@Z",
 "parampath_create": "?Create@TDB_ParamPathStream@@SAPEAVTDB_StreamBase@@AEBVTDB_MatchName@@PEAVTDB_StreamFactory@@_NI2@Z",
 "register": "?RegisterFactoryFunc@TDB_StreamFactory@@QEAA_NAEBVTDB_MatchName@@V?$function@$$A6APEAVTDB_StreamBase@@AEBVTDB_MatchName@@PEAVTDB_StreamFactory@@_NI2@Z@std@@_N@Z",
 "unregister": "?UnregisterFactoryFunc@TDB_StreamFactory@@QEAA_NAEBVTDB_MatchName@@@Z",
}
for year, f in targets.items():
    data = f.read_bytes()
    p = pefile.PE(data=data)
    sym = {e.name.decode():e.address for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
    print(year, hashlib.sha256(data).hexdigest())
    for k, name in names.items():
        assert name in sym, (year, name)
        rva=sym[name]
        off=p.get_offset_from_rva(rva)
        chunk = data[off:off+16]
        assert len(chunk)==16
        print(k, hex(rva), chunk.hex())
