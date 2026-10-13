"""Cross-check canonical CompItem attachment inbound sources vs stock factory.
Ensures the two layer materialization paths in AE2025/AE2026 are not
independent arbitrary-MatchName layer factories.
"""
from pathlib import Path
import json,pefile,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
cfg={
"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x2e3e10,[0x505090,0x505400],0x392120),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x2ecd00,[0x51f2f0,0x51f650],0x39d4d0)}
xrefs=json.loads(Path(r"D:\Developer\ShapeLayerAE\results\bee_native_compitem_attach_inbound_xrefs_2025_2026.json").read_text())["versions"]
ctx=json.loads(Path(r"D:\Developer\ShapeLayerAE\results\bee_comp_attach_caller_context_2025_2026.json").read_text())["versions"]
receipts={}
for year,(path,factory,loaders,attach) in cfg.items():
 raw=Path(path).read_bytes();p=pefile.PE(data=raw,fast_load=True);base=p.OPTIONAL_HEADER.ImageBase
 dis=Cs(CS_ARCH_X86,CS_MODE_64)
 mapped={int(x["function_rva"],16):x for x in ctx[year]}
 found=[]
 for begin in loaders:
  assert begin in mapped
  function=mapped[begin]
  size=int(function["referenced_comp_attach_sites"][0]["callsite"],16)-begin+256
  b=p.get_offset_from_rva(begin)
  inst=list(dis.disasm(raw[b:b+min(size,1200)],base+begin))
  creates=[int(i.address-base) for i in inst if i.mnemonic=="call" and i.op_str==hex(base+factory)]
  attaches=[int(i.address-base) for i in inst if i.mnemonic=="call" and i.op_str==hex(base+attach)]
  assert creates and attaches,(year,hex(begin),creates,attaches)
  assert max(creates)<min(attaches),(year,hex(begin))
  found.append({"caller_start":hex(begin),"fixed_native_factory_rva":hex(factory),
    "fixed_factory_callsites":[hex(n) for n in creates],
    "comp_attach_rva":hex(attach),"comp_attach_callsites":[hex(n) for n in attaches],
    "factory_called_before_attach":True})
 cloned=next(x for x in xrefs[year]["inbound_direct_xrefs"] if "CloneAndAttach@BEE_Layer" in x["caller_export"])
 assert cloned["caller_begin_rva"] not in [hex(x) for x in loaders]
 assert xrefs[year]["inbound_direct_xref_count"]==11
 receipts[year]={"BEE_SHA256":hashlib.sha256(raw).hexdigest(),
  "direct_comp_attach_xref_count":11,"unique_caller_function_count":len(mapped),
  "layer_file_materialization_paths":found,
  "clone_reattach_is_another_native_path":True,
  "foreign_subclass_construction_or_admission_confirmed":False,
  "published_sdk_extension_point_found":False}
 print("PASS",year,"both archive materialization paths call stock closed-type factory then CompItem attach",flush=True)
out=Path(r"D:\Developer\ShapeLayerAE\results\bee_comp_owner_load_routes_fixed_factory_verified_2025_2026.json")
out.write_text(json.dumps({"evidence":"E2-L native x64 direct callsite order in exact two BEE DLLs; not global proof of no other dispatch","versions":receipts},indent=2)+"\n")
print("SAVED",out)
