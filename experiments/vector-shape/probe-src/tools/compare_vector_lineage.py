"""Historical SDK 2012/2014/2025 & AE 2025/2026 BEE surface lineage.
E0-H and E2-L only: never invoke host-private code.
"""
from pathlib import Path
import re, subprocess, hashlib, json, time
out=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-shape-native-extension-lineage-2026.json")
base=Path(r"D:\Developer\After Effects Internals Guide")
sources={
"CS6":"research/external-sources/ae-sdk-cs6/Headers",
"CC2014":"research/external-sources/ae-sdk-cc2014/Headers",
"SDK25.6":r"E:\ae25.6_61.64bit.AfterEffectsSDK\Examples\Headers",
}
header_names=["AE_GeneralPlug.h","AE_EffectSuites.h","AE_GeneralPlugOld.h","AE_IO.h","AE_Effect.h"]
terms=["AEGP_StreamGroupingType","AEGP_GetNumStreamsInGroup","AEGP_GetNewStreamRefByIndex",
       "AEGP_AddStream","AEGP_CanAddStream","PF_PathQuerySuite","PF_PathDataSuite",
       "PF_Param_PATH","PF_Param_ARBITRARY_DATA","AEGP_Register", "AEGP_NewLayer",
       "AEGP_StreamFactory", "VectorArt", "AGM", "AEGP_CreateNew"]
sdkresults={}
for v,dr in sources.items():
    root=Path(dr) if ":" in dr else base/dr
    entries={}
    for fn in header_names:
        p=root/fn
        if not p.exists():continue
        lines=p.read_text(encoding="utf-8",errors="replace").splitlines()
        hits={}
        for term in terms:
            idx=[i+1 for i,line in enumerate(lines) if term in line]
            if idx:hits[term]=idx[:24]
        entries[fn]={"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"hits":hits}
    sdkresults[v]=entries

dlls={
"AE2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
"AE2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"),
}
bins={}
for k,path in dlls.items():
    if not path.is_file():continue
    cp=subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,errors="replace",check=False)
    if cp.returncode!=0:raise RuntimeError((k,cp.stderr[:350]))
    lines=cp.stdout.splitlines()
    pattern=re.compile(r"^\s*\d+\s+[0-9A-F]+\s+[0-9A-F]{8}\s+")
    exports=[line.strip() for line in lines if pattern.match(line)]
    categories={
        "constructor_generic_shape":"??0BEE_GenericShapeStream@@",
        "tbd_stream_factory":"TDB_StreamFactory",
        "populate_vector_art":"PopulateVectorArt",
        "rasterize_2d":"Rasterize2DGraph",
        "vector_art_getbounds":"GetBounds@BEE_VectorArt",
        "vector_stream":"BEE_VectorStream",
        "type_registration_names":"Register.*Stream|Register.*Factory|Create.*StreamFactory|Add.*StreamFactory|New.*StreamFactory",
        "AGM_port":"AGMPort|AGMDisplayList|CAGMPath",
    }
    matches={}
    for label,q in categories.items():
        target=re.compile(q if label in ('type_registration_names', 'AGM_port') else re.escape(q))
        hits=[line for line in exports if target.search(line)]
        matches[label]={"count":len(hits),"examples":hits[:18]}
    bins[k]={"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
             "file_size":path.stat().st_size,
             "export_count":len(exports),
             "category_hits":matches}
report={"classification":"E0-H historical public headers; E2-L static runtime exports",
        "claim_boundary":"Version-specific presence/absence within scanned scopes; NOT proof of callable private APIs, nor exhaustive private registration",
        "historical_public_headers":sdkresults,
        "runtime_exports":bins,
        "sources":{v:str((Path(d) if ":" in d else base/d)) for v,d in sources.items()}}
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("saved",out)
for v,files in sdkresults.items():
    print("SDK",v)
    for fname,obj in files.items():
        print("  ",fname,"  ", " ".join(f"{s}:{len(ln)}" for s,ln in obj["hits"].items()))
for v,obj in bins.items():
    print("BINARY",v,obj["sha256"],"exports",obj["export_count"])
    for cat,hit in obj["category_hits"].items():
        print("  ",cat,hit["count"])
        if cat in ("constructor_generic_shape","populate_vector_art","type_registration_names","rasterize_2d"):
            for line in hit["examples"][:6]:print("    ",line[:175])
