"""Verify native Effect nested-group admission and canonical UI schema.
Fully offline pinned PE/COFF checks; no private ABI calls and no project edits.
"""
from pathlib import Path
import json
r=Path(r"D:\Developer\ShapeLayerAE\results")
schema=json.loads((r/"flt_fcseqspec_nested_schema_2025_2026.json").read_text())["versions"]
vtable=json.loads((r/"flt_fcseqspec_child_canstore_vtable_2025_2026.json").read_text())["versions"]
proof={}
for year in ("2025","2026"):
 def func(mod,needle):
  a=[v for v in schema[year][mod]["functions"] if needle in v["name"]]
  assert len(a)==1,(year,mod,needle,len(a))
  return a[0]
 can=func("TDB","?CanStore@TDB_StreamGroup@@")
 setup=func("TDB","?SetupCanonicalLayout@TDB_StreamGroup@@")
 seq=func("FLT","?FillInCanonicalUILayout@FLT_FCSeqSpec@@")
 builtin=func("FLT","?FillInCanonicalUILayout@FLT_EffectBuiltInParams@@")
 compound=func("FLT","?FillInCanonicalUILayout@FLT_CompoundEffect@@")
 v=vtable[year]
 assert v["tdb_canstore_slot"]==56
 assert v["resolved_import"]=="TDB.dll!?CanStore@TDB_StreamGroup@@UEBA_NAEBVTDB_MatchName@@@Z"
 assert len(seq["instructions"])==1 and seq["instructions"][0]["m"]=="ret"
 for field in ("[rcx + 0x210]","[rcx + 0x218]"):
  assert any(field in x["args"] for x in can["instructions"]),(year,field)
 assert any("??8TDB_MatchName@@" in x["symbol"] for x in can["edges"])
 assert any(x["m"]=="setne" for x in can["instructions"])
 assert any(x["m"]=="call" and "[rax + 0x1c8]" in x["args"] for x in setup["instructions"])
 for name in ("?SetupCanonicalLayoutForSeperatedDimensions@TDB_StreamFactory@@",
              "?SetUILayout@TDB_StreamGroup@@"):
  assert any(name in x["symbol"] for x in setup["edges"]),(year,name)
 getter="GetCanonicalStream@TDB_StreamBase@@"
 assert sum(getter in x["symbol"] for x in builtin["edges"])>=3
 assert sum(getter in x["symbol"] for x in compound["edges"])>=2
 proof[year]={"verified_fcseqspec_nested_canstore_uses_tdb_streamgroup":True,
  "nested_canstore_virtual_slot":56,
  "canonical_list_owner_fields":["0x210","0x218"],
  "setup_calls_canonical_fill_virtual_offset":"0x1c8",
  "flt_fcseqspec_fill_canonical_layout_noop":True,
  "flt_effect_builtin_fills_via_canonical_streams":True,
  "third_party_can_extend_host_canonical_layout":False,
  "native_renderer_or_pen_integrated":False,
  "tdb_sha256":schema[year]["TDB"]["sha256"],"flt_sha256":schema[year]["FLT"]["sha256"]}
 print("PASS",year,"FCSeqSpec CanStore inherited TDB canonical-match admission, self fill no-op")
dest=r/"flt_fcseqspec_nested_admission_verified_2025_2026.json"
dest.write_text(json.dumps({"classification":"E2-L cross-version static proof; not third-party extension","versions":proof},indent=2)+"\n")
print("SAVED",dest)
