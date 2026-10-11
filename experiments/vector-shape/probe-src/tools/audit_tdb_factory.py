"""AE 2025/2026 TDB.dll private stream-factory and indexed-group API surface.
Only local binary export/PE-import metadata. No private API invocation.
"""
from pathlib import Path
import subprocess,re,pefile,json,hashlib,collections
modules={
"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\TDB.dll"),
"2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\TDB.dll")}
regex=re.compile(r"^\s*(\d+)\s+([0-9A-Fa-f]+)\s+([0-9A-Fa-f]{8})\s+(\S+)")
classes=["TDB_StreamFactory","TDB_ScRegisterStreams","TDB_IndexedStreamGroup","TDB_NamedStreamGroup","TDB_StreamGroup","TDB_StreamBase","TDB_UniqueIdHelper","TDB_StreamIDPath"]
terms=["Register","Unregister","Create","CanStore","GetCanonical","AddStreamToUILayout","Store","Remove","Insert","Move","Reorder","UILayout","MatchName","GetFactory"]
results={}
for v,path in modules.items():
    cp=subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,errors="replace",check=True)
    symbols=[]
    for line in cp.stdout.splitlines():
        m=regex.match(line)
        if m:symbols.append({"ordinal":int(m.group(1)),"rva":m.group(3),"name":m.group(4)})
    byclass={}
    for c in classes:
        own=[s for s in symbols if re.search(r"(?:\?|[?][?][01])[^@]*@"+re.escape(c)+r"@@",s["name"])]
        # Many methods contain nested template paths, do not claim completeness.
        byclass[c]={"export_matches":len(own),"sample":own[:250]}
    tdbfactory=[s for s in symbols if s["name"].startswith("?") and "@TDB_StreamFactory@@" in s["name"]]
    filters={term:[s for s in tdbfactory if term in s["name"]] for term in terms}
    pe=pefile.PE(str(path))
    deps=[{"dll":im.dll.decode(errors="replace"),"n":len(im.imports)} for im in pe.DIRECTORY_ENTRY_IMPORT]
    results[v]={"module":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes":path.stat().st_size,"total_exports":len(symbols),
                "classes":byclass,
                "factory_own_export_count":len(tdbfactory),
                "factory_owned_methods":tdbfactory,
                "factory_verb_groups":{k:len(x) for k,x in filters.items()},
                "imports":deps}
target=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-tdb-native-stream-factory-2025-2026.json")
target.write_text(json.dumps({"grade":"E2-L static binary export artifact","not":"Supported SDK/API, callable private extension, or confirmed runtime behavior","versions":results},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("OUTPUT",target)
for v,o in results.items():
    print("\n==",v,"hash",o["sha256"],"EXPORTS",o["total_exports"])
    for c,x in o["classes"].items():print(c,x["export_matches"])
    print("FACTORY OWNED",o["factory_own_export_count"])
    for s in o["factory_owned_methods"]:print(" ",s["rva"],s["name"][:200])
