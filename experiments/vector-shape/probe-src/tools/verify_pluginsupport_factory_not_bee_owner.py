"""Pinned PluginSupport generic module factory vs native BEE Layer evidence.
Only PE metadata, no dynamic module loading, calls or hooks.
"""
from pathlib import Path
import json,hashlib,re,subprocess,pefile
ROOT=Path(__file__).resolve().parents[4]
CONFIG={
 "2025":{"dll":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\PluginSupport.dll",
 "sha256":"2f43339ad7f5a8c8655a291f6dac0580d95a2e79db38d74272a9e5d83b3fe049"},
 "2026":{"dll":r"D:\Adobe\Adobe After Effects 2026\Support Files\PluginSupport.dll",
 "sha256":"cb73d45bad03f26684b88f78353a558d8ceb4aea73a3a3e163f457b574e01f5c"}
}
out={}
for year,c in CONFIG.items():
 p=Path(c["dll"]);raw=p.read_bytes()
 assert hashlib.sha256(raw).hexdigest()==c["sha256"],(year,"DLL revision changed")
 pe=pefile.PE(data=raw)
 imported=sorted({mod.dll.decode(errors="replace") for mod in pe.DIRECTORY_ENTRY_IMPORT})
 assert not any(m.lower() in ("bee.dll","tdb.dll") for m in imported)
 text=subprocess.run(["dumpbin","/exports",str(p)],capture_output=True,text=True,errors="replace",check=True).stdout
 exports={}
 for line in text.splitlines():
  m=re.match(r"^\s*\d+\s+[0-9a-fA-F]+\s+([0-9a-fA-F]{8})\s+(\S+)",line)
  if m:exports[m.group(2)]=hex(int(m.group(1),16))
 exact=[x for x in exports if x.startswith("?RegisterPluginModuleFactory@ML@@")]
 assert len(exact)==1,(year,exact)
 name=exact[0]
 assert "Guid@utility@dvacore" in name
 assert "UIPluginModuleFactory@ML" in name
 assert "BEE_Layer" not in name and "TDB_Stream" not in name
 assert not any("BEE_Layer" in k or "BEE_VectorLayer" in k for k in exports)
 loader_names=[{"name":k,"rva":v} for k,v in exports.items() if "PluginLoaderRegistry@ML" in k or "RegisterPluginModuleFactory@ML" in k]
 out[year]={"sha256":c["sha256"],"export_count":len(exports),
 "plugin_module_registration_symbol":name,"registration_rva":exports[name],
 "import_modules":imported,
 "direct_imports_BEE_or_TDB":False,
 "matched_ML_registry_symbols":loader_names,
 "evidence_limit":"No proof of no indirect linkage or all host layer-provider mechanisms"}
 print("PASS",year,"ML PluginSupport.dll module factory takes Guid + UIPluginModuleFactory",
       "no BEE/TDB direct module imports","exports",len(exports))
dest=ROOT/"datasets"/"ae-pluginsupport-ml-plugin-factory-vs-bee-layer-2025-2026.json"
dest.write_text(json.dumps({"scope":"Exact installed PE exported signatures and imported modules, not dynamic linkage census","versions":out},indent=2)+"\n",encoding="utf-8")
print("OUTPUT",dest)
