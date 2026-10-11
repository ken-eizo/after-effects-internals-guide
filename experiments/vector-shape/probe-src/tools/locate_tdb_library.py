import pefile,json
from pathlib import Path
p=Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")
pe=pefile.PE(str(p))
info=[]
for x in pe.DIRECTORY_ENTRY_IMPORT:
    name=x.dll.decode("utf-8","replace")
    matched=[r.name.decode("utf-8","replace") for r in x.imports if r.name and (b"TDB_" in r.name or b"StreamFactory" in r.name)]
    if matched:info.append({"module":name,"imports":len(x.imports),"TDB_matches":len(matched),"examples":matched[:90]})
q=Path(r"D:\Developer\ShapeLayerAE\results\tdb_import_ownership.json")
q.write_text(json.dumps(info,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps([{"module":i["module"],"matches":i["TDB_matches"],"total":i["imports"]} for i in info]))
