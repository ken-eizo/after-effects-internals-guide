"""Independent cross-check of host-native generic stream editing and shape/mask reset.
No Adobe private call or native plugin installation.
"""
from pathlib import Path
import json
root=Path(r"D:\Developer\ShapeLayerAE\results")
a=json.loads((root/"native_vector_generic_stream_write_contract_2025_2026.json").read_text())["versions"]
b=json.loads((root/"shared_shape_mask_edit_helper_2025_2026.json").read_text())["versions"]
kind={}
for y in ("2025","2026"):
 entries=a[y]["functions"]
 def get(name):
  r=[x for x in entries if x["name"].startswith(name)]
  assert len(r)==1,(y,name,len(r))
  return r[0]
 mask=get("?BEE_CmdResetMaskShape@@")
 shape=get("?BEE_CmdResetVectorShape@@")
 m={c["destination_rva"] for c in mask["calls"]}
 s={c["destination_rva"] for c in shape["calls"]}
 common=m&s
 assert b[y]["entry"] in common,(y,common)
 helper=b[y]["direct_calls"]
 def count(rows,label):
  return sum(label in x["symbol"] for x in rows)
 assert count(helper,"?BEE_StartGroup@@")==1
 assert count(helper,"?BEE_EndGroup@@")==1
 assert count(helper,"?BEE_CmdSetStreamFPVPlus@@")>=4
 assert count(helper,"?BEE_DoCommand@@")>=1
 writer=get("?BEE_CmdSetStreamFPVPlus@@")
 for symbol in ("?BEE_GetStreamWithSpec@@","?BEE_StreamTypeHasStream@@",
                "?BEE_StartGroupNamed@@","?BEE_SetStreamFPV@@",
                "?BEE_DoCommand@@","?BEE_EndGroup@@"):
  assert count(writer["calls"],symbol)>=1,(y,symbol)
 kind[y]={"BEE_sha256":a[y]["sha256"],"reset_mask_and_vector_same_helper":b[y]["entry"],
          "generic_value_writer":writer["rva"],
          "generic_value_writer_calls":["BEE_GetStreamWithSpec","BEE_StreamTypeHasStream",
            "BEE_StartGroupNamed","BEE_SetStreamFPV","BEE_DoCommand","BEE_EndGroup"],
          "native_pen_drag_callback_proven":False,"external_owner_proven":False}
 print("PASS",y,": shared Mask/Vector reset helper and BEE_Layer* stream write+undo",flush=True)
dst=root/"verified_shared_native_edit_contract_2025_2026.json"
dst.write_text(json.dumps({"classification":"E2-L exact native code xrefs; public AE SDK extension not established",
 "versions":kind},indent=2)+"\n",encoding="utf8")
print("SAVED",dst)
