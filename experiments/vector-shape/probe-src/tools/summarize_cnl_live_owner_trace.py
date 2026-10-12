"""Summarise the user's genuine in-AE read-only owner trace.
Never publish all unrelated AE project property names.
"""
from pathlib import Path
import os,json,re
p=Path(os.environ["TEMP"])/"CNL_NativeOwner_Admission.tsv"
lines=p.read_text(encoding="utf-8").splitlines()
assert lines[0].startswith("# EXP-SHAPE-039 READ ONLY")
stream={}
children={}
adm={}
footer={}
for line in lines[1:]:
 parts=line.split("\t")
 if parts[0]=="stream":
  _,idx,depth,parent,name,kind,err=parts
  stream[int(idx)]={"depth":int(depth),"parent":parent,"name":name,"group_kind":int(kind),"error":int(err)}
 elif parts[0]=="parent_link":
  _,child,parent=parts
  children[int(child)]=int(parent)
 elif parts[0]=="admission":
  _,idx,name,result,err=parts
  adm.setdefault(int(idx),{})[name]=(int(result),int(err))
 elif len(parts)==2:
  footer[parts[0]]=parts[1]
effect_nodes=[i for i,s in stream.items() if s["name"]=="CNL Owned Vector Document" and s["parent"]=="ADBE Effect Parade"]
assert len(effect_nodes)==1,effect_nodes
eff=effect_nodes[0]
kids=[{"name":stream[i]["name"],"kind":stream[i]["group_kind"],"depth":stream[i]["depth"]} for i,par in children.items() if par==eff]
assert sorted(k["name"] for k in kids if k["kind"]==0)==[f"CNL Owned Vector Document-{i:04d}" for i in range(5)]
assert any(k["name"]=="ADBE Effect Built In Params" for k in kids)
assert int(footer["visited_nodes"])==len(stream)==173
assert footer["private_registry_invoked"]=="0" and footer["stream_created"]=="0"
parade_ids=[i for i,s in stream.items() if s["name"]=="ADBE Effect Parade"]
assert len(parade_ids)==1
dataids=[i for i,s in stream.items() if s["name"]=="ADBE Data Group"]
summary={"date":"2026-10-12","source":"User-run read-only AE2026 AEGP report, not another offline binary dump",
 "effect_loaded_and_attached_to_host_effect_parade":True,
 "effect_match_name":"CNL Owned Vector Document",
 "effect_group_kind":stream[eff]["group_kind"],
 "effect_param_names":[v["name"] for v in kids if v["kind"]==0],
 "effect_param_count_visible_as_leaves":5,
 "builtin_effect_params_group_present":True,
 "stream_visited":len(stream),
 "private_registration":False,
 "stream_creation":False,
 "candidate_adhoc_group_admitted_under_effect":adm[eff]["CNL Native Independent Group"][0],
 "adobe_slider_admitted_under_top_level_effect_parade":adm[parade_ids[0]]["ADBE Slider Control"][0],
 "candidate_adhoc_group_admitted_under_top_level_effect_parade":adm[parade_ids[0]]["CNL Native Independent Group"][0],
 "host_render_verified_by_this_report":False,
 "host_project_save_reopen_verified_by_this_report":False,
 "host_native_CNL_vertex_contents":False,
 "warning":"AEGP_CanAddStream returns only an eligibility boolean, not actual construction or registration, particularly for generic Data Group"}
dest=Path(r"D:\Developer\ShapeLayerAE\results\cnl_owned_effect_live_host_trace_sanitized_20261012.json")
dest.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(summary,ensure_ascii=False,indent=2))
print("SAVED",dest)
