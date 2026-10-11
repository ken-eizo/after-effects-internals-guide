"""Portable AEIG verifier for private Shape owner/raster ABI research.
Only publishes FACTS (RVA, ABI slot, allocation sizes, versions/hashes), not
full proprietary instructions/vftable images. Raw static outputs remain local
and can be re-derived with the cited original scripts.
"""
import json
from pathlib import Path
root=Path(r"D:\Developer\After Effects Internals Guide")
def load(s):
 return json.loads((root/"datasets"/s).read_text(encoding="utf-8"))
v=load("ae-native-av-vs-vector-layer-raster-vtable-2025-2026.json")
a=load("ae-native-shape-layer-command-type-adapter-2025-2026.json")
l=load("ae-vector-layer-native-owner-vs-avlayer-render-2025-2026.json")
c=load("ae-native-vector-layer-creation-adapter-target-2025-2026.json")
expected={"2025":{"slot":235,"av_size":0x2810,"vec_size":0x2820,"cmd":0x65},
          "2026":{"slot":238,"av_size":0x27d8,"vec_size":0x2830,"cmd":0x6a}}
compact={}
for year,wanted in expected.items():
    yearv="AE"+year
    vr=v["versions"][yearv];ar=a["versions"][year];lr=l["versions"][yearv];cr=c["versions"][year]
    rvas=vr["rvas"]
    av=vr["vtables"]["av_vtable"]["entries"]
    vec=vr["vtables"]["vector_vtable"]["entries"]
    def selected(entries,k):
        hits=[e for e in entries if e["target_rva"]==rvas[k]]
        assert len(hits)==1,(year,k,hits)
        return hits[0]["slot_index"]
    assert selected(av,"av_raster")==wanted["slot"]
    assert selected(vec,"vector_raster")==wanted["slot"]
    assert selected(av,"av_type")==80
    assert selected(vec,"vector_type")==80
    def commands(name):
        group=[x for x in ar["functions"] if name in x["query"]]
        assert len(group)==1,(year,name,len(group))
        return group[0]["instructions"]
    def exact(ops,opcode,needle):
        return any(o["mnemonic"]==opcode and needle in o["operands"] for o in ops)
    assert exact(commands("GetLayerType@BEE_VectorLayer"),"mov","eax, 4")
    assert exact(commands("GetLayerType@BEE_AVLayer"),"xor","eax, eax")
    assert exact(commands("GetDefaultTypeMagic@BEE_VectorLayer"),"mov","0x5192004")
    assert exact(commands("?Create@BEE_VectorLayer"),"mov",f"ecx, 0x{wanted['vec_size']:x}")
    assert exact(commands("?Create@BEE_AVLayer"),"mov",f"ecx, 0x{wanted['av_size']:x}")
    cmdops=commands("?BEE_CmdNewVectorLayer")
    assert exact(cmdops,"mov",f"edx, 0x{wanted['cmd']:x}")
    assert exact(cmdops,"mov","r8d, 0x306")
    assert any(f["query"]=="?Create@BEE_VectorLayer@@" and
               any("??0BEE_VectorLayer" in q["symbol"] for q in f.get("calls",[]))
               for f in lr["results"])
    assert any(f["query"]=="?Create@BEE_AVLayer@@" and
               any("??0BEE_AVLayer" in q["symbol"] for q in f.get("calls",[]))
               for f in lr["results"])
    assert any(row["target"]==hex(0x667610 if year=="2025" else 0x682f90)
       and any("BEE_DoCommand" in i["resolved"] for i in row["assembly"])
       for row in cr["trace"])
    compact[yearv]={
      "source_bee_sha256":vr["sha256"],
      "av_vtable_rva":rvas["av_vtable"],
      "vector_vtable_rva":rvas["vector_vtable"],
      "raster_slot_index":wanted["slot"],
      "raster_slot_byte_offset":hex(wanted["slot"]*8),
      "av_raster_function_rva":rvas["av_raster"],
      "vector_raster_function_rva":rvas["vector_raster"],
      "layer_type_slot_index":80,
      "ordinary_av_layer_type":0,"shape_vector_layer_type":4,
      "vector_default_type_magic":"0x05192004",
      "av_layer_allocated_bytes":wanted["av_size"],
      "vector_layer_allocated_bytes":wanted["vec_size"],
      "vector_native_newlayer_command_id":hex(wanted["cmd"]),
      "vector_native_newlayer_resource_id":"0x306",
      "producer_creator_is_native_tdb_callback":True,
      "third_party_creator_registration_proven":False,
      "effect_native_geometry_output_proven":False
    }
dest=root/"datasets"/"ae-native-vector-owner-contract-summary-2025-2026.json"
dest.write_text(json.dumps({
 "classification":"E2-L machine code corroboration, compact fact-only digest",
 "goal":"Third-party effect-owned editable native path, new Contents, native VectorArt output without Mask/Shape layer dependence",
 "success_gate":"not yet achieved; only internal native class/render contract reconstructed",
 "source_raw_local_only":["ae-native-av-vs-vector-layer-raster-vtable-2025-2026.json",
                          "ae-vector-layer-native-owner-vs-avlayer-render-2025-2026.json",
                          "ae-native-shape-layer-command-type-adapter-2025-2026.json",
                          "ae-native-vector-layer-creation-adapter-target-2025-2026.json"],
 "versions":compact},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("PASS: Layer owner and renderer ABI data independently cross-validated",list(compact))
for version,fields in compact.items():
 print(version,"raster slot",fields["raster_slot_index"],"av bytes",
       fields["av_layer_allocated_bytes"],"vector bytes",fields["vector_layer_allocated_bytes"])
print("SAVED",dest)
