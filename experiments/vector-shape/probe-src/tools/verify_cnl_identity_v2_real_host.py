"""Verify AE2026 live v2 rerun against the previous v1 failing run.
Keep published evidence to relevant CNL data only.
"""
from pathlib import Path
import os,json
home=Path(os.environ["TEMP"])
def load(file):
 f=home/file
 rows=[line.split("\t") for line in f.read_text(encoding="utf-8").splitlines() if line and not line.startswith("#")]
 return rows
a=load("CNL_OwnedEffect_StreamIdentity.tsv")
b=load("CNL_OwnedEffect_StreamIdentity_v2.tsv")
def single(rows,name):
 x=[r for r in rows if r[0]==name]
 assert len(x)==1,(name,x)
 return x[0]
assert single(a,"target_effect")==single(b,"target_effect")==["target_effect","0","5","0"]
assert single(b,"matched_CNL_effects")==["matched_CNL_effects","1"]
assert single(b,"param_skipped")==["param_skipped","0","input_layer_host_rejects_index_zero"]
p1={int(r[1]):r for r in a if r[0]=="param"}
p2={int(r[1]):r for r in b if r[0]=="param"}
assert set(p1)==set(range(5))
assert set(p2)=={1,2,3,4}
assert all(p1[i]==p2[i] for i in range(1,5)),"one of the valid parameter results changed"
assert p1[0][3]=="3" and p1[0][9]=="3"
for idx,r in p2.items():
 assert r[3]=="0" and r[5]=="0" and r[8]=="0" and r[9]=="0" and r[10]=="0" and r[12]=="0"
 assert r[6]=="0","unique ID wasn't zero"
assert (p2[1][2],p2[1][4])==("11","7")
for key,value in {"private_registry_invoked":"0","mutations":"0","opaque_arb_payload_read":"0"}.items():
 assert single(b,key)==[key,value]
result={
 "experiment":"EXP-SHAPE-053",
 "date":"2026-10-12",
 "evidence":"AE2026 user-run v1 and v2 TSV log comparison",
 "v1_bad_queries_0":2,
 "v2_has_no_queries_0":True,
 "v2_effect_count":1,
 "v2_total_params_including_input":5,
 "v2_valid_param_indices":[1,2,3,4],
 "v2_all_valid_rows_match_v1":True,
 "v2_all_valid_query_errors_zero":True,
 "v2_arb_param_index":1,
 "v2_arb_pf_type":11,
 "v2_arb_aegp_stream_type":7,
 "v2_unique_stream_ids":[0,0,0,0],
 "v2_private_registry_invoked":False,
 "v2_project_mutations":False,
 "v2_opaque_arb_payload_read":False,
 "runtime_failed_to_emit_report":False,
 "native_pen_edit_tested":False,
 "aep_save_reopen_tested":False
}
dest=Path(r"D:\Developer\ShapeLayerAE\results\cnl_owned_identity_v2_real_host_verified_20261012.json")
dest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("PASS real AE2026 v2: index0 eliminated; all four valid params byte-for-byte agree with v1")
print("ARB 11/7, metadata errors=0, IDs all zero; no mutations")
print("SAVED",dest)
