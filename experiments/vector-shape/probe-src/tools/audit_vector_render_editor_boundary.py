"""Targeted inventory of host-native shape geometry, selection, and presentation functions.
No binary content copied; only normalized exported name+RVA/symbol metadata.
"""
from pathlib import Path
import subprocess,re,json,hashlib
bins={"AE2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
"AE2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
rx=re.compile(r"^\s*(\d+)\s+([0-9A-Fa-f]+)\s+([0-9A-Fa-f]{8})\s+(\S+)")
filters={
"vector_art_model":[r"@BEE_VectorArt@@",r"@BEE_VectorArt::",r"@OriginInfo@BEE_VectorArt@@"],
"geometry_evaluator":[r"PopulateVectorArt",r"GetVectorArt@BEE_VectorLayer",r"GetBounds@BEE_VectorArt",r"GetVectorLayer",r"BEE_IllusShapeTarget"],
"native_vector_registration":[r"RegisterStreams@BEE_Vector",r"Register.*Vector",r"Create.*Vector",r"Factory.*Vector",r"Get_AE_StreamFactory"],
"native_selection_tool":[r"BEE_GetSelectedShapePathsVec",r"IsPathOrChildSelected",r"Shape.*(Select|Tool|Edit|Hit|Pick)",r"(Select|Tool|Edit|Hit|Pick).*Shape",r"Path.*(Select|Tool|Edit|Hit|Pick)"],
"native_renderer":[r"C_AGMDLTranslatePort",r"BEE_SVGToAGM",r"Rasterize2DGraph@BEE_VectorLayer",r"AGMDisplayList",r"RenderVectorArt",r"RenderShape"],
"generic_shape":[r"@BEE_GenericShapeStream@@",r"@VectorsStreamGroup@BEE_VectorStream@@"]
}
results={}
for version,path in bins.items():
    p=Path(path)
    cp=subprocess.run(["dumpbin","/exports",str(p)],capture_output=True,text=True,errors="replace",check=True).stdout
    exports=[]
    for l in cp.splitlines():
        m=rx.match(l)
        if m:exports.append({"rva":m.group(3),"name":m.group(4)})
    groups={}
    for category,reg in filters.items():
        pats=[re.compile(x,re.I) for x in reg]
        matches=[x for x in exports if any(pt.search(x["name"]) for pt in pats)]
        groups[category]={"total":len(matches),"symbols":matches if len(matches)<300 else matches[:300]}
    results[version]={"BEE_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"exports":len(exports),"categories":groups}
out=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-native-vector-render-edit-boundary-2025-2026.json")
out.write_text(json.dumps({"evidence":"E2-L static export names; no private host API call","versions":results},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("OUTPUT",out)
for v,r in results.items():
    print("=== ",v)
    for c,g in r["categories"].items():
        print("---",c,g["total"])
        for s in g["symbols"][:50]:
            print(" ",s["rva"],s["name"][:185])
