"""Independent full native Shape Layer -> Root Vectors -> Contents schema proof,
matching real BEE static MatchName constructors and 183 native TDB registration
calls for both pinned Adobe versions. No private calls or AE mutations.
"""
from pathlib import Path
import json
base=Path(r"D:\Developer\ShapeLayerAE\results")
schema=json.loads((base/"bee_vector_native_layer_contents_allowed_children_2025_2026.json").read_text())["versions"]
literal=json.loads((base/"bee_native_vector_group_schema_matchname_literal_init_2025_2026.json").read_text())["versions"]
typed=json.loads((base/"bee_vector_layer_62_native_tdb_creators_2025_2026.json").read_text())["versions"]
corpus=json.loads((base/"bee_native_vector_three_level_canonical_schema_cross_verified_2025_2026.json").read_text())["versions"]
pipeline=json.loads((base/"bee_native_vector_all183_tdb_registration_pipeline_2025_2026.json").read_text())["versions"]
out={};names_by_version={}
for y in ("2025","2026"):
 def lit(address):
  rows=literal[y].get(address,[])
  found={entry["text"] for x in rows for entry in x["literals"]}
  assert len(found)==1,(y,address,found)
  return next(iter(found))
 cls=schema[y]["three_schema_classes"]
 layer,root,contents=cls
 l=[{"matchname":lit(x["last_matchname_arg"]["matchname_rva"]),
     "native_matchname_object_rva":x["last_matchname_arg"]["matchname_rva"],
     "lookup_rva":x["callsite"]} for x in layer["canonical_children"]]
 r=[{"matchname":lit(x["last_matchname_arg"]["matchname_rva"]),
     "native_matchname_object_rva":x["last_matchname_arg"]["matchname_rva"],
     "lookup_rva":x["callsite"]} for x in root["canonical_children"]]
 c=corpus[y]["contents_canonical_types_in_native_order"]
 assert [x["matchname"] for x in r]==["ADBE Vector Blend Mode","ADBE Vectors Group",
   "ADBE Vector Transform Group","ADBE Vector Materials Group"]
 assert l[1]["matchname"]=="ADBE Root Vectors Group"
 assert len(l)==(10 if y=="2025" else 11)
 assert len(r)==4 and len(c)==20
 assert pipeline[y]["total_static_registration_calls"]==183
 assert "ADBE Vector Group"==c[0]
 roots=typed[y]["entries"]
 assert r[1]["native_matchname_object_rva"]==roots[59]["match"]["data_rva"]
 assert r[2]["native_matchname_object_rva"]==roots[56]["match"]["data_rva"]
 assert r[3]["native_matchname_object_rva"]==roots[48]["match"]["data_rva"]
 assert l[1]["native_matchname_object_rva"]==roots[60]["match"]["data_rva"]
 assert "Create@VectorsStreamGroup@BEE_VectorStream" in roots[60]["creator"]["symbol"]
 assert "Create@VectorsStreamGroup@BEE_VectorStream" in roots[59]["creator"]["symbol"]
 assert roots[60]["creator"]["data_rva"]==roots[59]["creator"]["data_rva"]
 assert "Create@VectorStreamGroup@BEE_VectorStream" in roots[58]["creator"]["symbol"]
 assert "Create@BEE_VectorLayer@@" in roots[61]["creator"]["symbol"]
 assert set(c)==set(pipeline[y]["operator_matchnames_joined_to_native_TDB_creator_registration"])
 out[y]={"BEE_SHA256":schema[y]["BEE_SHA256"],
 "native_owner":"BEE_VectorLayer",
 "native_layer_canonical_children":l,
 "native_root_vectors_matchname":"ADBE Root Vectors Group",
 "native_root_vector_stream_group_class":"VectorStreamGroup",
 "native_root_vector_group_four_children":r,
 "native_contents_matchname":"ADBE Vectors Group",
 "native_contents_group_class":"VectorsStreamGroup",
 "native_contents_twenty_allowed_children":c,
 "all_20_contents_elements_are_real_TDB_type_registered":True,
 "native_matchname_root_owner_creator":"BEE_VectorLayer::Create",
 "native_matchname_root_vectors_creator":"BEE_VectorStream::VectorsStreamGroup::Create",
 "native_matchname_contents_group_creator":"BEE_VectorStream::VectorsStreamGroup::Create",
 "native_static_TDB_register_calls":183,
 "CNL_plugin_defined_native_type_created":False}
 names_by_version[y]={"layer":[x["matchname"] for x in l],"root":[x["matchname"] for x in r],"contents":c}
 print("PASS",y,"native Shape level",len(l),"root",len(r),"Contents",len(c),flush=True)
 print("  root layer canonical",names_by_version[y]["layer"],flush=True)
assert names_by_version["2025"]["root"]==names_by_version["2026"]["root"]
assert names_by_version["2025"]["contents"]==names_by_version["2026"]["contents"]
old=names_by_version["2025"]["layer"];new=names_by_version["2026"]["layer"]
assert [v for v in new if v not in old]==["ADBE Layer Credential ID"]
assert [v for v in old if v not in new]==[]
outpath=base/"bee_native_shape_canonical_hierarchy_named_verified_2025_2026.json"
outpath.write_text(json.dumps({"evidence":"E2-L exact installed native BEE: MatchName static constructors + 3 native virtual UILayout bodies + TDB canonical instances + 183 typed creator sites","versions":out,
"cross_version":{"contents_20_same_order":True,"root_4_same_order":True,
"layer_canonical_added_2026":["ADBE Layer Credential ID"]},
"unproven":["third-party native stream registration","CNL-owned layer or Contents accepted","Pen/Selection native edit integration","BEE_VectorArt render output from CNL"]},ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("SAVED",outpath)
