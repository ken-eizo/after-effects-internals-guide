"""Cross-check EXP-SHAPE-014/015/016 against independent static evidence.
Pure dataset validation, no DLL executed and no AE process modified.
"""
from pathlib import Path
import json,hashlib
ROOT=Path(r"D:\Developer\After Effects Internals Guide")
def dataset(name):return json.loads((ROOT/"datasets"/name).read_text(encoding="utf-8"))["versions"]
ident=dataset("ae-vector-evaluator-matchname-identities-2025-2026.json")
rtti=dataset("ae-native-vector-evaluator-vtable-rtti-2025-2026.json")
slots=dataset("ae-vector-evaluator-vtable-slot-map-2025-2026.json")
modes=dataset("ae-vector-evaluator-mode-abi-2025-2026.json")
bases=dataset("ae-native-vector-operator-rtti-inheritance-2025-2026.json")
origins=dataset("ae-vector-operator-vectorart-provenance-calls-2025-2026.json")
evidence={}
for version in ("2025","2026"):
 a=ident[version]["records"]
 names=[x["name"] for x in a]
 assert len(names)==len(set(names))==20,version
 rs=slots[version]["rows"]
 assert [x["matchName"] for x in rs]==names
 modes_rows=modes[version]["entries"]
 assert [x["MatchName"] for x in modes_rows]==names
 assert (modes[version]["mode0_count"],modes[version]["mode1_count"])==(9,11)
 assert sum(x["kind"]=="native-filter-mode-1" for x in modes_rows)==11
 assert sum(x["kind"]=="native-shape-graphic-mode-0" for x in modes_rows)==9
 inherit=bases[version]["rows"]
 assert [x["matchName"] for x in inherit]==names
 class_names={}
 for row,base in zip(rs,inherit):
  assert len(row["tables"])>=2,(version,row["matchName"],"missing secondary")
  offsets={t["subobject_offset"] for t in row["tables"]}
  assert {0,24}.issubset(offsets),(version,row["matchName"],offsets)
  table=next(t for t in base["tables"] if t["subobject_offset"]==0)
  chain=" ".join(c["class"] for c in table["rtti_hierarchy"]["bases"])
  assert "Operator@BEE_VectorStream" in chain and "RefCountedInterface" in chain
  class_names[row["matchName"]]=row["concrete_rtti"]
 origin_entries={x["matchName"]:x for x in origins[version]["entries"]}
 path_receipts={}
 for key,converter in [
  ("ADBE Vector Shape - Group","GetPathDataFromOM"),
  ("ADBE Vector Shape - Rect","GetRectPathData"),
  ("ADBE Vector Shape - Ellipse","GetEllipsePathData")]:
  item=origin_entries[key];slot=next(x for x in item["slots"] if x["slot"]==4)
  calls=" ".join(c["symbol"] for c in slot["calls"])
  for symbol in (converter,"Path@BEE_VectorArt","OriginInfo@BEE_VectorArt","SetOriginInfo@BaseObject@BEE_VectorArt"):
   assert symbol in calls,(version,key,symbol)
  path_receipts[key]=slot["begin_rva"]
 repeat=origin_entries["ADBE Vector Filter - Repeater"]
 rep5=next(x for x in repeat["slots"] if x["slot"]==5)
 syn=[c["site"] for c in rep5["calls"] if "AppendSyntheticIndex@OriginInfo@BEE_VectorArt" in c["symbol"]]
 assert len(syn)>=2,(version,"Repeater",syn)
 assert any("SymbolGroup@BEE_VectorArt" in c["symbol"] for c in rep5["calls"])
 evidence[version]={"exactly_20_unique_MatchNames":True,
                    "type_name_order_matches_rtti_and_modes":True,
                    "nine_native_geometry_mode_zero":True,
                    "eleven_native_filters_mode_one":True,
                    "primary_and_secondary_vtable_0_and_24_for_all":True,
                    "reference_counted_operator_base_rtti_for_all":True,
                    "path_rect_ellipse_contain_bezier_and_origin_sequences":path_receipts,
                    "repeater_synthetic_index_direct_calls":syn,
                    "concrete_classes":class_names}
assert evidence["2025"]["concrete_classes"]==evidence["2026"]["concrete_classes"],"cross-version class mismatch"
evidence["cross_version_exact_concrete_classes_equal"]=True
dest=ROOT/"datasets/ae-vector-operator-independent-crosscheck-2025-2026.json"
dest.write_text(json.dumps({"classification":"E2-L independent dataset consistency checks only; no host code execution","checks":evidence},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("PASS: 2 versions x 20 native evaluator registrations and vtables; 9/11 evaluation modes; 3 Bezier+Origin conversion types; 2+ Repeater synthetic-index callsites each.")
print("SAVED:",dest)
