"""Identify *own* TDB factory exports, vector-specific methods and registration candidates.
Only PE export inventory; keep exact symbols in analysis dataset.
"""
import subprocess,re,json,hashlib
from pathlib import Path
bins={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
      "2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
rx=re.compile(r"^\s*(\d+)\s+([0-9A-Fa-f]+)\s+([0-9A-Fa-f]{8})\s+(\S+)")
checks={
"owned_factory_methods":re.compile(r"(?:@TDB_StreamFactory@@|[?][?]0TDB_StreamFactory@@|[?][?]1TDB_StreamFactory@@)"),
"type_registration":re.compile(r"(?:Register|Add|Create|New|Install).*?(?:Stream|Shape|Vector)|(?:Stream|Shape|Vector).*?(?:Register|Factory|Creator|Dispatcher)"),
"shape_commands":re.compile(r"@BEE_VectorStream@@|@BEE_VectorLayer@@|BEE_CmdNewVectorLayer|BEE_CmdReorderIndexedGroupEntry"),
"selection":re.compile(r"Select.*(?:Shape|Path)|(?:Shape|Path).*Select|HitTest|Pick.*Vector|Find.*Shape"),
}
result={}
for version,p in bins.items():
    s=subprocess.run(["dumpbin","/exports",p],capture_output=True,text=True,errors="replace",check=True).stdout
    exports=[]
    for line in s.splitlines():
        m=rx.match(line)
        if m:exports.append({"ordinal":int(m.group(1)),"rva":m.group(3),"name":m.group(4)})
    groups={}
    for title,regex in checks.items():
        hits=[e for e in exports if regex.search(e["name"])]
        if title=="owned_factory_methods":
            groups[title]={"count":len(hits),"hits":hits[:100]}
        elif title=="type_registration":
            groups[title]={"count":len(hits),"hits":hits[:250]}
        else:
            groups[title]={"count":len(hits),"hits":hits[:40]}
    result[version]={"groups":groups}
dest=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-shape-factory-registration-candidates-2025-2026.json")
dest.write_text(json.dumps({"scope":"Static BEE export inventory only. TDB_StreamFactory in parameter positions is not factory-owned API.","versions":result},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
for v,o in result.items():
    print("\n==",v)
    for k,g in o["groups"].items():
        print(k,g["count"])
        if k in ("type_registration","owned_factory_methods"):
            for x in g["hits"][:80]:print(" ",x["rva"],x["name"][:170])
print("SAVED",dest)
