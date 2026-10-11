"""E2-L pin the direct runtime DynamicStreamEffectsParser::EndEffect
 -> TDB_StreamGroup::AddStreamToUILayout calls, not IAT jump stubs.
 Compare AE2025/2026. No host/private API execution.
"""
import json
from pathlib import Path
root=Path(r"D:\Developer\ShapeLayerAE\results")
raw=json.loads((root/"flt_addstream_to_uilayout_crossmodule_direct_sites_2025_2026.json").read_text())["years"]
out={}
for year in ("2025","2026"):
 b=raw[year]["BEE.dll"]
 records=[x for x in b["static_sites"]
  if "TDB.dll!?AddStreamToUILayout@TDB_StreamGroup@@" in x["import"]
  and "EndEffect@DynamicStreamEffectsParser@" in x["caller_export"]]
 assert len(records)==2,(year,records)
 assert all(x["instruction"]=="call" for x in records)
 for x in records:
  ctx=x["context"]
  match=next((i for i,t in enumerate(ctx) if t["rva"]==x["site"]),None)
  assert match is not None
  prefix=ctx[max(0,match-8):match]
  regs=[t["args"] for t in prefix]
  assert "rcx, rax" in regs
  assert any(n.startswith("rdx,") for n in regs)
  assert any(n.startswith("r8d,") for n in regs)
 others=[x for x in b["static_sites"]
   if "AddStreamToUILayout" in x["import"] and x["instruction"]=="jmp"]
 frp=raw[year].get("FRP.dll",{})
 frp_sites=[x for x in frp.get("static_sites",[])
  if "FLT_FCSeqSpec@@UEBAX" in x["import"]]
 assert frp_sites and all(x["instruction"]=="jmp" for x in frp_sites)
 out[year]={"BEE_sha256":b["sha256"],
 "direct_end_effect_calls":[{"callsite":x["site"],"function":x["caller_export"],
                            "reg_setup":x["context"]} for x in records],
 "BEE_AddStream_import_jump_thunks":len(others),
 "FRP_FLT_AddStream_import_jump_thunks":len(frp_sites),
 "FLT_FCSeqSpec_AddStream_direct_call_proven_in_FRP":False}
 print("PASS",year,"two direct BEE DynamicStreamEffectsParser::EndEffect calls; FRP entry is only a thunk")
dest=root/"verified_bee_dynamic_effect_parser_layout_2025_2026.json"
dest.write_text(json.dumps({"evidence":"E2-L code calls validated separately from imported JMP trampolines","years":out},indent=2)+"\n",encoding="utf8")
print("SAVED",dest)
