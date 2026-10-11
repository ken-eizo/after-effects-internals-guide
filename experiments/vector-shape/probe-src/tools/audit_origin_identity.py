"""Static, read-only x64 export inventory for vector origin/selection/AGM interaction.
Artifact only: do not infer an external plugin ABI.
"""
from pathlib import Path
import json,hashlib,subprocess,re
P={
"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
"2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")
}
terms={
"origin_stream_id":"OriginInfo@BEE_VectorArt",
"synthetic_origin":"Synthetic|SynthIDPath",
"layer_select_display_list":"LayerSelectSetupPrePlayback|LayerSelectTeardown|GetLayerFilterProc|C_AGMDLTranslatePort",
"vector_evaluation":"PopulateVectorArt|GetVectorArt@BEE_VectorLayer|GetBounds@BEE_VectorArt",
"layer_selection":"FindClosestMaskSnapPoint|FindClosest.*Shape|HitTest.*Vector|Pick.*Vector|Select.*Path",
"factory_registration":"RegisterStreams@BEE_VectorLayer|RegisterStreams@BEE_TextLayer|RegisterStreams@BEE_Layer"
}
pattern=re.compile(r"^\s*(\d+)\s+([0-9A-Fa-f]+)\s+([0-9A-Fa-f]{8})\s+(\S+)")
out={"evidence":"E2-L binary export artifact only","scope":"AE2025 and AE2026 BEE.dll; no dynamic runtime calls","modules":{}}
for k,p in P.items():
    cp=subprocess.run(["dumpbin","/exports",str(p)],capture_output=True,text=True,errors="replace",check=True)
    exports=[]
    for line in cp.stdout.splitlines():
        m=pattern.match(line)
        if m:exports.append({"ordinal":int(m.group(1)),"rva":m.group(3),"decorated":m.group(4)})
    groups={}
    for g,q in terms.items():
        reg=re.compile(q)
        rows=[x for x in exports if reg.search(x["decorated"])]
        groups[g]={"count":len(rows),"symbols":rows[:100]}
    out["modules"][k]={"dll":str(p),"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"export_count":len(exports),"categories":groups}
p=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-vector-origin-identity-2025-2026.json")
p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",p)
for v,o in out["modules"].items():
    print("==",v,o["sha256"])
    for name,group in o["categories"].items():
        print(name,"n",group["count"])
        for e in group["symbols"][:12]:print(" ",e["rva"],e["decorated"][:145])
