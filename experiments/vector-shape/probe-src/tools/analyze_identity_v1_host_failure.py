"""Parse the user's actual CNL identity v1 TSV. Keep only CNL result,
never publish unrelated effect match-name or project details.
Confirm that ONLY index0 returned API errors and supported indices 1-4 passed.
"""
from pathlib import Path
import os,json
src=Path(os.environ["TEMP"])/"CNL_OwnedEffect_StreamIdentity.tsv"
rows=[line.split("\t") for line in src.read_text(encoding="utf-8").splitlines() if line]
def single(k):
 v=[x for x in rows if x[0]==k]
 assert len(v)==1,(k,v)
 return v[0]
assert single("match_target")[1]=="CNL Owned Vector Document"
assert single("effect_count_error")[1]=="0"
assert single("effect_count")[1]=="1"
assert single("target_effect")[1:]==["0","5","0"]
assert single("matched_CNL_effects")[1]=="1"
assert single("private_registry_invoked")[1]=="0"
assert single("mutations")[1]=="0"
assert single("opaque_arb_payload_read")[1]=="0"
items=[r for r in rows if r[0]=="param"]
assert [int(r[1]) for r in items]==list(range(5))
summary=[]
for r in items:
 _,idx,pf,pe,vt,te,unique,variable,ve,re,ie,name,me=r
 record={"index":int(idx),"pf_type":int(pf),"pf_error":int(pe),
 "aegp_stream_type":int(vt),"stream_type_error":int(te),
 "unique_stream_id_result":int(unique),"timevarying":int(variable),
 "timevarying_error":int(ve),"stream_ref_error":int(re),
 "unique_stream_id_error":int(ie),"match_error":int(me)}
 if int(idx)==0:
  assert record["pf_error"]==3 and record["stream_ref_error"]==3
 else:
  assert record["pf_error"]==record["stream_ref_error"]==0
  assert record["stream_type_error"]==record["timevarying_error"]==0
  assert record["unique_stream_id_error"]==record["match_error"]==0
  assert record["unique_stream_id_result"]==0
 summary.append(record)
assert summary[1]["pf_type"]==11 and summary[1]["aegp_stream_type"]==7
assert [x["aegp_stream_type"] for x in summary[1:]]==[7,5,6,5]
out={"run":"AE2026 actual user-run identity probe v1","source":"real %TEMP% CNL_OwnedEffect_StreamIdentity.tsv",
 "observed_internal_assertion":"AE error dialogs 5027::56 and 5027::150 param_index out of range",
 "cause":"both GetEffectParamUnionByIndex and GetNewEffectStreamByIndex on param_index 0 returned A_Err=3",
 "confirmed_effect_count":1,"confirmed_param_stream_count":5,
 "param_results":summary,
 "native_opaque_arb_param1_confirmed":True,"all_indices_1_through_4_pass":True,
 "no_unique_ids_observed_all_supported_returned_zero":True,
 "project_modified_by_probe":False,
 "host_ae2026_archive_save_reopen_tested":False,
 "correction":"v2 skips index 0 entirely; emits param_skipped 0, uses _v2.tsv name"}
dest=Path(r"D:\Developer\ShapeLayerAE\results\cnl_identity_v1_host_error_sanitized_20261012.json")
dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("PASS real AE2026 TSV: invalid idx0; idx1 = ARB; idx1..4 metadata all pass; IDs 0")
print("SAVED",dest)
