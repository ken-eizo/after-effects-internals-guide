"""Bounded read-only AE2026 cross-module import inventory for native
FLT_FCSeqSpec::AddStreamToUILayout and FLT parameter/sequence APIs.
No host functions are called. Only installed on-disk PE imports are parsed.
"""
from pathlib import Path
import pefile,json,hashlib
root=Path(r"D:\Adobe\Adobe After Effects 2026\Support Files")
files=sorted(list(root.glob("*.dll"))+list(root.glob("*.exe")))
terms=("AddStreamToUILayout","GetChildParamDef","GetParamTable",
       "FLT_RegisterPseudoEffect","RegisterFactoryFunc@TDB_StreamFactory")
results=[];failed=[];count=0
for file in files:
 try:
  p=pefile.PE(str(file),fast_load=True)
  p.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]])
  count+=1
  for lib in getattr(p,"DIRECTORY_ENTRY_IMPORT",[]):
   dll=lib.dll.decode(errors="replace")
   for imp in lib.imports:
    if not imp.name:continue
    name=imp.name.decode(errors="replace")
    if any(t in name for t in terms):
     results.append({"module":file.name,"imported_dll":dll,"symbol":name})
 except Exception as e:
  failed.append({"name":file.name,"error":type(e).__name__})
 if count%75==0: print("scanned",count,"matched",len(results),flush=True)
path=Path(r"D:\Developer\ShapeLayerAE\results\ae2026_flt_addlayout_crossmodule_import_inventory.json")
path.write_text(json.dumps({"classification":"E2-L executable import tables only; indirect/virtual/dynamic loading excluded",
 "root":str(root),"scan_scope":"direct Support Files DLL/EXE, no nested plugin dirs",
 "scanned":count,"failed":failed,"matches":results},indent=2)+"\n",encoding="utf8")
print("FINISHED scanned",count,"matches",len(results),"failed",len(failed),flush=True)
for hit in results:print(hit["module"],hit["imported_dll"],hit["symbol"][:120],flush=True)
print("SAVED",path)
