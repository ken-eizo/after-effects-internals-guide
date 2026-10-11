"""Cross-version closed native BEE Layer factory case contract.
Reads static forensic receipts only. No private Adobe function calls.
"""
from pathlib import Path
import json,hashlib
p=Path(r"D:\Developer\ShapeLayerAE\results\native_layer_factory_type_dispatch_2025_2026.json")
data=json.loads(p.read_text(encoding="utf8"))["versions"]
expected=("BEE_AVLayer","BEE_LightLayer","BEE_CameraLayer","BEE_TextLayer",
          "BEE_VectorLayer","BEE_ModelLayer","BEE_ParametricMeshLayer")
report={}
for yr in ("2025","2026"):
 block=data[yr]
 ops=block["instructions"]
 constructors={}
 for op in ops:
  target=op.get("export","")
  for kind in expected:
   if target.startswith("??0"+kind+"@@"):constructors.setdefault(kind,[]).append(op["rva"])
 assert set(constructors)==set(expected),(yr,constructors)
 assert all(len(v)==1 for v in constructors.values()),(yr,constructors)
 assert any(x["m"]=="cmp" and x["args"].endswith(", 7") for x in ops)
 assert any(x["m"]=="jmp" and x["args"] in ("rcx","rdx") for x in ops)
 # This one routine has 7 direct concrete constructors, no external
 # factory callback. Negative is scoped to THIS dispatcher only.
 others=[x for x in ops if x.get("export","").startswith("??0BEE_") and "Layer@@" in x.get("export","")]
 assert len(others)==7,(yr,others)
 beta=any("BEE_BetaFeature_Is3DParametricMeshEnabled" in x.get("export","") for x in ops)
 report[yr]={"sha256":block["BEE_sha256"],"bound_seven":True,
             "concrete_direct_constructors":constructors,"beta_feature_guard_call":beta,
             "external_custom_layer_constructor_in_this_dispatcher":False}
 print("PASS",yr,": seven direct native constructors, integer <=7 dispatch","beta_mesh",beta)
out=Path(r"D:\Developer\ShapeLayerAE\results\native_layer_factory_closed_switch_verification.json")
out.write_text(json.dumps({"classification":"E2-L static current-installed BEE CreateLayerFromType scope only",
"does_not_prove":"No other native type extension mechanism anywhere in AE","versions":report},indent=2)+"\n",encoding="utf8")
print("SAVED",out)
