"""Read-only native TDB registrar import graph across all installed Adobe PE modules.
Does not load/execute Adobe code, alter AE, or publish user-installed third-party names.
"""
from pathlib import Path
import pefile,collections,json,re
ROOTS={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files"),
       "2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files")}
TARGETS={
 "TDB_ScRegisterStreams_Register":"?Register@TDB_ScRegisterStreams@@",
 "TDB_StreamFactory_RegisterFactoryFunc":"?RegisterFactoryFunc@TDB_StreamFactory@@",
 "TDB_StreamFactory_UnregisterFactoryFunc":"?UnregisterFactoryFunc@TDB_StreamFactory@@",
 "TDB_ScRegisterStreams_UnregisterAll":"?UnregisterAll@TDB_ScRegisterStreams@@",
 "BEE_Layer_RegisterStreams":"?RegisterStreams@BEE_Layer@@",
 "BEE_VectorLayer_RegisterStreams":"?RegisterStreams@BEE_VectorLayer@@"
}
res={}
for year,root in ROOTS.items():
 paths=sorted(set(p for ext in ("*.dll","*.exe","*.aex") for p in root.rglob(ext)))
 count=collections.Counter();hits=collections.defaultdict(list);fail=[];total=0
 for p in paths:
  try:
   pe=pefile.PE(str(p),fast_load=True)
   pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]])
   total+=1
   for desc in getattr(pe,"DIRECTORY_ENTRY_IMPORT",[]):
    dll=desc.dll.decode(errors="replace").lower()
    for imp in desc.imports:
     if not imp.name:continue
     s=imp.name.decode(errors="replace")
     for typ,pattern in TARGETS.items():
      if s.startswith(pattern):
       count[typ]+=1
       # Only host first-party top-level module identity is recorded publicly.
       if p.parent==root:
        hits[typ].append({"module":p.name,"from_dll":dll,"import":s})
       else:
        hits[typ].append({"module_class":"non-top-level binary","from_dll":dll,"import":s})
  except Exception as e:fail.append(str(type(e).__name__))
  if total%300==0:print(year,"parsed",total,"/",len(paths),flush=True)
 assert total>=850,(year,total)
 print("===",year,total,"targets",dict(count),"fail",len(fail),flush=True)
 for key,v in hits.items():
  x=sorted({z.get("module",z.get("module_class","")) for z in v})
  print(" ",key,":",x[:45],flush=True)
 res[year]={"PE_files_discovered":len(paths),"PE_files_parsed":total,
            "PE_parse_failures":dict(collections.Counter(fail)),
            "direct_import_count_by_api":dict(count),
            "host_modules_with_direct_registrar_imports":dict(hits)}
out=Path(__file__).resolve().parents[4]/"datasets"/"ae-native-tdb-registrar-import-graph-2025-2026.json"
out.write_text(json.dumps({"scope":"All installed .dll/.exe/.aex under After Effects Support Files, direct PE import table only, privacy-scoped",
                           "limitations":["Dynamic imports and API suites are not inspected","Direct import does not prove active callsite nor supported external ABI"],"results":res},indent=2)+"\n",encoding="utf-8")
print("PASS",out)
