"""ABI drift proof across AE2025/AE2026 native BEE_Layer::CloneAndAttach.
Strict E2-L offline native-machine instruction check; no Adobe host execution.
"""
from pathlib import Path
import json,hashlib,pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
configs={"2025":{"dll":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll","entry":0x2e20e0,
"comp_load":"mov rcx, qword ptr [rbp + 0x2b8]","flag_vcall":"call qword ptr [rdx + 0x2a8]",
"attach_call":"call 0x1803920f0","cloned_type_field":None},
"2026":{"dll":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll","entry":0x2eb090,
"comp_load":"mov rcx, qword ptr [rbp + 0x260]","flag_vcall":"call qword ptr [rdx + 0x2b8]",
"attach_call":"call 0x18039d4a0","cloned_type_field":"mov rdi, qword ptr [rbx + 0x260]"}}
out={}
for y,c in configs.items():
 raw=Path(c["dll"]).read_bytes();p=pefile.PE(data=raw,fast_load=True);base=p.OPTIONAL_HEADER.ImageBase
 dec=Cs(CS_ARCH_X86,CS_MODE_64)
 a=c["entry"];b=a+(0x180 if y=="2025" else 0x1b0)
 inst=list(dec.disasm(raw[p.get_offset_from_rva(a):p.get_offset_from_rva(b)],base+a))
 patterns={i.mnemonic+" "+i.op_str:[hex(i.address-base)] for i in inst}
 sites={}
 for key in ["comp_load","flag_vcall","attach_call"]:
  text=c[key]
  matches=[hex(i.address-base) for i in inst if i.mnemonic+" "+i.op_str==text]
  assert len(matches)==1,(y,key,text,matches)
  sites[key]=matches[0]
 assert int(sites["flag_vcall"],16)<int(sites["comp_load"],16)<int(sites["attach_call"],16),y
 # C++ this owner pointer is saved in RBP at function entry.
 assert any(i.mnemonic=="mov" and i.op_str=="rbp, rcx" for i in inst[:10])
 if c["cloned_type_field"]:
  assert any(i.mnemonic+" "+i.op_str==c["cloned_type_field"] for i in inst)
 out[y]={"sha256":hashlib.sha256(raw).hexdigest(),"CloneAndAttach_entry":hex(a),
 "CompItem_this_member_offset":hex(0x2b8 if y=="2025" else 0x260),
 "BEE_Layer_virtual_flag_slot":hex(0x2a8 if y=="2025" else 0x2b8),
 "instruction_sites":sites,
 "BEE_Layer_CompItem_pointer_layout_stable":False,
 "BEE_Layer_vtable_slot_stable":False,
 "true_native_foreign_class_created":False}
 print("PASS",y,"BEE layer Comp ptr",out[y]["CompItem_this_member_offset"],"flag vcall",out[y]["BEE_Layer_virtual_flag_slot"],flush=True)
assert out["2025"]["CompItem_this_member_offset"]!=out["2026"]["CompItem_this_member_offset"]
assert out["2025"]["BEE_Layer_virtual_flag_slot"]!=out["2026"]["BEE_Layer_virtual_flag_slot"]
dest=Path(r"D:\Developer\ShapeLayerAE\results\bee_layer_clone_attach_cross_version_abi_drift_verified_2025_2026.json")
dest.write_text(json.dumps({"evidence":"E2-L different native C++ object layout and vtable offsets across two pinned actual Adobe BEE builds; not public ABI","versions":out},indent=2)+"\n")
print("SAVED",dest)
