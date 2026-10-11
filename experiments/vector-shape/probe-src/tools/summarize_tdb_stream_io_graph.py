from pathlib import Path
import json
p=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-tdb-native-clone-serialization-parent-callgraph-2025-2026.json")
j=json.loads(p.read_text(encoding="utf-8"))
for year,ver in j["versions"].items():
 print("\nYEAR",year)
 for name in ("clone_base","clone_leaf","clone_parampath","read_group","write_group","read_leaf","write_leaf","parent_base","canonical_layout","indexed_append"):
  f=ver["methods"][name]
  print("\n ",name,"RVA",f.get("rva"),"len",f.get("bounded_bytes"))
  for c in f.get("resolved_calls",[]):
   sym=c["resolved"]
   if any(k in sym for k in (
    "GetCanonical","CreateStream","Create@","Clone","Copy","Read@","Write@","ReadUnique","WriteUnique","MatchName","SLU_BeginChunkWrite","SLU_EndChunkWrite","SLU_ReadAtom","SLU_WriteAtom","SetParent","SetDisplay","GetDisplay","GetStream","StreamID","InsertStream","AppendStream","SetUILayout","GetKeyData","GetExpression","HasKeys","GetCache","SetConstant")):
    print("   ",c["site"],sym[:135])
  print(" INDIRECT",f.get("indirect_virtual_calls",[])[:11])
