"""Check compiled AEGP -> standalone geometry -> SVG: real cubic paths, no raster.
Run two times and reject fake static SVG generation if shapes do not change.
Does not attempt to claim AE SVG import itself is verified.
"""
from pathlib import Path
from xml.etree import ElementTree as ET
import math, re, subprocess,hashlib,json
ROOT=Path(r"D:\Developer\ShapeLayerAE")
AEIG=Path(r"D:\Developer\After Effects Internals Guide")
exe=ROOT/"build/vector_bridge/Release/VectorBridgeToSVG.exe"
provider=ROOT/"build/vector_bridge/Release/VectorBridgeAEGP.aex"
dest=ROOT/"results/CNL_Vector_Rosette_28.svg"
dest0=ROOT/"results/CNL_Vector_Rosette_28_t0.svg"
for out,t in [(dest,12),(dest0,0)]:
 result=subprocess.run([str(exe),str(provider),str(out),str(t),"24","1","28"],capture_output=True,text=True,check=True)
 assert "PASS native_pica_aex=1" in result.stdout
 assert "rendered_paths=28" in result.stdout
ns={"s":"http://www.w3.org/2000/svg"}
reports={}
for t,path in [("12/24",dest),("0/24",dest0)]:
 doc=ET.parse(path);root=doc.getroot()
 paths=root.findall("s:path",ns)
 assert len(paths)==28,len(paths)
 assert len({x.get("id") for x in paths})==28
 assert not list(root.iter("{http://www.w3.org/2000/svg}image"))
 assert not list(root.iter("{http://www.w3.org/2000/svg}foreignObject"))
 for i,x in enumerate(paths):
  v=x.attrib["d"]
  assert v.count("C ")==4,(i,v)
  assert v.count("M ")==1 and v.strip().endswith("Z")
  assert x.attrib["fill"]=="none"
  assert "stroke" in x.attrib and "stroke-width" in x.attrib
  numbers=[float(n) for n in re.findall(r"[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?",v)]
  assert len(numbers)==26,(i,len(numbers))
  assert all(math.isfinite(a) and -20<a<1044 for a in numbers),(i,numbers)
 reports[t]={"path":str(path),"svg_path_elements":28,"cubic_segments":28*4,
             "pixel_image_elements":0,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
             "first_path_d":paths[0].get("d")}
assert reports["0/24"]["sha256"]!=reports["12/24"]["sha256"]
assert reports["0/24"]["first_path_d"]!=reports["12/24"]["first_path_d"]
receipt=AEIG/"datasets/ae-pica-vector-svg-rosette-geometry-validation-2026.json"
receipt.write_text(json.dumps({"classification":"E2-T actual compiled provider AEX independently loaded and vector SVG generated in standalone executable; no After Effects SVG import host claim",
                            "time_snapshots":reports,"cross_time_geometry_changed":True,
                            "native_contents_or_ae_vector_output_proven":False},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("PASS 28 unique vector paths, 112 cubics, no raster <image>, 2 distinct time samples")
print("SAVED",receipt)
