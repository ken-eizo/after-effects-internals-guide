"""Map native TDB C++ virtual slots actually called during eager registration.

Read PE vftables from exact installed AE2025/AE2026 TDB.dll and BEE.dll.
No host execution or binary modifications.
"""
from pathlib import Path
import pefile,subprocess,re,struct,hashlib,json
paths={
"2025":{
"TDB.dll":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\TDB.dll"),
"BEE.dll":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll")},
"2026":{
"TDB.dll":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\TDB.dll"),
"BEE.dll":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")}
}
regex=re.compile(r"^\s*\d+\s+[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s+(\S+)")
selectors=["TDB_StreamBase","TDB_Stream","TDB_StreamGroup",
           "TDB_IndexedStreamGroup","TDB_NamedStreamGroup"]
targets=[0x58,0x80,0x90,0x150]
report={}
for ver,modules in paths.items():
 vtables={}
 for module,path in modules.items():
  raw=path.read_bytes();p=pefile.PE(data=raw);base=p.OPTIONAL_HEADER.ImageBase
  symbols={}
  for line in subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,errors="replace",check=True).stdout.splitlines():
   m=regex.match(line)
   if m:symbols[int(m.group(1),16)]=m.group(2)
  for name in selectors:
   matches=[(addr,s) for addr,s in symbols.items() if s==f"??_7{name}@@6B@"]
   if len(matches)!=1:continue
   rva=matches[0][0]
   entries={}
   for offset in targets + ([0x190,0x298] if name=='TDB_Stream' else ([0x190] if name in ('TDB_NamedStreamGroup','TDB_IndexedStreamGroup') else [])):
    addr=rva+offset
    try:ptr=struct.unpack_from("<Q",raw,p.get_offset_from_rva(addr))[0]
    except Exception:continue
    trva=ptr-base
    exported=symbols.get(trva,"")
    executable=any(bool(s.Characteristics & 0x20000000) and
       s.VirtualAddress<=trva<s.VirtualAddress+s.Misc_VirtualSize for s in p.sections)
    entries[hex(offset)]={"index":offset//8,"function_rva":hex(trva),
      "exported_symbol":exported if executable else "",
      "target_executable":bool(executable)}
   vtables[name]={"module":module,"rva":hex(rva),"slots":entries}
   print(ver,module,name,"selected slots",
       [(x,ent["exported_symbol"][:105] if ent["exported_symbol"] else ent["function_rva"])
           for x,ent in entries.items()],flush=True)
 report[ver]={"TDB_hash":hashlib.sha256(modules["TDB.dll"].read_bytes()).hexdigest(),
  "BEE_hash":hashlib.sha256(modules["BEE.dll"].read_bytes()).hexdigest(),
  "tables":vtables}
dest=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-tdb-stream-vtable-creator-required-methods-2025-2026.json")
dest.write_text(json.dumps({"evidence":"E2-L native exported vftable slots", "versions":report},
  ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dest,flush=True)
