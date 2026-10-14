from pathlib import Path
import pefile,collections,json
roots={
 "2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files"),
 "2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files")
}
out={}
registrars=(
 "?Register@TDB_ScRegisterStreams@@",
 "?RegisterFactoryFunc@TDB_StreamFactory@@",
 "?UnregisterFactoryFunc@TDB_StreamFactory@@",
 "?RegisterStreams@BEE_AVLayer@@",
 "?RegisterStreams@BEE_Layer@@"
)
for year,root in roots.items():
 files=sorted(set((root/"Required").rglob("*.aex"))|set((root/"Plug-ins").rglob("*.aex")))
 stats=collections.Counter()
 findings=[]
 names={"Paint.aex","Paint Palette.aex","Roto Brush.aex","SVGImporter.aex","AEGPDriver.aex","Cineware_AE_SceneLayer.aex"}
 selected={}
 errors=[]
 for p in files:
  try:
   pe=pefile.PE(str(p),fast_load=True)
   pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]])
   imports={}
   for d in getattr(pe,"DIRECTORY_ENTRY_IMPORT",[]):
    dll=d.dll.decode(errors="replace").lower()
    imports[dll]=[i.name.decode(errors="replace") if i.name else "#"+str(i.ordinal) for i in d.imports]
   for dll in ("tdb.dll","bee.dll","afterfxlib.dll","pluginsupport.dll"):
    if dll in imports:stats[dll]+=1
   for dll,names2 in imports.items():
    hits=[s for s in names2 if any(s.startswith(sig) for sig in registrars)]
    if hits:findings.extend({"module_classification":"Required" if (root/"Required") in p.parents else "Plug-ins",
                            "library":dll,"registrar":s} for s in hits)
   if p.name in names:
    selected[p.name]={"required":(root/"Required") in p.parents,"imports_tdb":("tdb.dll" in imports),"imports_bee":("bee.dll" in imports)}
  except Exception as exc:errors.append(str(exc)[:180])
 assert len(files)>400,year
 assert not errors,errors[:5]
 assert not findings, (year,findings[:10])
 out[year]={
  "installed_aex_files":len(files),"all_import_table_parsed":True,
  "direct_tdb_importers":stats["tdb.dll"],
  "direct_bee_importers":stats["bee.dll"],
  "direct_native_factory_register_importers":len(findings),
  "registrar_symbols_searched":list(registrars),
  "selected_adobe_bundled_module_categories":selected
 }
 print(year, "AEX",len(files), "direct TDB",stats["tdb.dll"],"direct BEE",stats["bee.dll"],"registrar imports",len(findings),flush=True)
output=Path(r"D:\Developer\ShapeLayerAE\labs\paint_native_properties_audit\adobe_installed_aex_native_registrar_imports_2025_2026_aggregate.json")
payload={
 "date":"2026-10-14",
 "coverage":"All installed AEX under Required and Plug-ins, including user third-party add-ons; aggregate only",
 "privacy":"No third-party plugin names or file paths are stored in the published dataset",
 "scope_limitations":["Direct PE import table ONLY. Dynamic symbol lookup, delay import directories and host-provided suite mechanisms not excluded",
                      "Adobe built-in Paint stream registry runs from BEE.dll startup; external TDB class admission still unproven",
                      "Cineware scene AEX name does NOT establish BEE_Layer class registration"],
 "versions":out
}
output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("PASS, saved aggregate",output)
