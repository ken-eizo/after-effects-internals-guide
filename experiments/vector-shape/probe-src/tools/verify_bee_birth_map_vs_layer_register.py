"""Verify two distinct BEE_Birth inputs: byte-map init vs built-in layer registrars.
Only offline installed Adobe native DLLs, no private Adobe calls.
"""
from pathlib import Path
import pefile,hashlib,json,bisect
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
ROOT=Path(__file__).resolve().parents[4]
CONFIG={
"2025":{"dll":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
"sha256":"98c682351e30f38cb7021eaa142f5ec473aea92885e14915d87c157cda971730",
"birth":0x64a530,"saved_map":"[rsp + 0x38]","saved_bytes":"[rsp + 0x158]","map_call":0x64aac9,"map_helper":0x11bee0,
"register_call":0x64aae0,"register_helper":0x36dd90},
"2026":{"dll":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",
"sha256":"5fd8d318456228b9fd2a6733a5758f6b84206b7a8effcba5202957cd27ac680e",
"birth":0x664f70,"saved_map":"[rsp + 0x88]","saved_bytes":"[rsp + 0x40]","map_call":0x665507,"map_helper":0x122910,
"register_call":0x66551b,"register_helper":0x3787b0}}
report={}
for year,c in CONFIG.items():
 raw=Path(c["dll"]).read_bytes()
 assert hashlib.sha256(raw).hexdigest()==c["sha256"], (year,"Unexpected Adobe binary revision")
 pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase
 pdata=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in pe.DIRECTORY_ENTRY_EXCEPTION)
 starts=[a for a,b in pdata]
 md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
 imports={i.address:desc.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace")
          for desc in pe.DIRECTORY_ENTRY_IMPORT for i in desc.imports if i.name}
 def body(entry):
  ix=bisect.bisect_right(starts,entry)-1
  assert ix>=0 and entry<pdata[ix][1]
  a,b=pdata[ix]
  result=[]
  for ins in md.disasm(raw[pe.get_offset_from_rva(entry):pe.get_offset_from_rva(b)],base+entry):
   target=None
   if ins.mnemonic in ("call","jmp") and ins.operands:
    x=ins.operands[0]
    if x.type==X86_OP_IMM:target=x.imm
    elif x.type==X86_OP_MEM and x.mem.base==X86_REG_RIP:target=ins.address+ins.size+x.mem.disp
   result.append({"at":ins.address-base,"asm":ins.mnemonic+" "+ins.op_str,
                  "target":None if target is None else target-base,
                  "import":imports.get(target,"")})
  return result
 birth=body(c["birth"])
 positions={row["at"]:i for i,row in enumerate(birth)}
 mi,ri=positions[c["map_call"]],positions[c["register_call"]]
 assert mi<ri and 0<ri-mi<20,(year,mi,ri)
 map_call=birth[mi];reg_call=birth[ri]
 assert map_call["target"]==c["map_helper"],(year,map_call)
 assert reg_call["target"]==c["register_helper"],(year,reg_call)
 assert birth[mi-1]["asm"]=="mov rcx, qword ptr "+c["saved_map"],(year,birth[mi-1])
 assert birth[ri-1]["asm"]=="mov rcx, qword ptr "+c["saved_bytes"],(year,birth[ri-1])
 helper=body(c["map_helper"])
 names=[row["import"] for row in helper if row["import"]]
 has_localizer=any("Localizer@ScCore" in name for name in names)
 has_scripting=any("InitTerm@ScScript" in name for name in names)
 assert has_localizer and has_scripting,(year,names)
 assert not any("TDB_ScRegisterStreams" in n or "RegisterFactoryFunc" in n for n in names)
 print("PASS",year,"BEE_Birth distinct map->init and bytePtr->type registrar",
       hex(c["map_call"]),hex(c["register_call"]),"Localizer",has_localizer,
       "ScScript",has_scripting)
 report[year]={"sha256":hashlib.sha256(raw).hexdigest(),
  "map_input_forwarded_at":hex(c["map_call"]),"map_helper_rva":hex(c["map_helper"]),
  "byte_input_forwarded_at":hex(c["register_call"]),"builtin_type_registrar_rva":hex(c["register_helper"]),
  "map_helper_imports_sc_localizer":has_localizer,
  "map_helper_imports_sc_script":has_scripting,
  "map_helper_direct_tdb_registrar_imports_observed":False,
  "boundary_rows":[{"rva":hex(row["at"]),"asm":row["asm"],"target":None if row["target"] is None else hex(row["target"])}
     for row in birth[mi-1:mi+2]+birth[ri-1:ri+2]],
  "not_proven":"Full data-map semantics, indirect paths, external Layer class registration or safe private ABI"}
dest=ROOT/"datasets"/"ae-bee-birth-map-versus-layer-bootstrap-2025-2026.json"
dest.write_text(json.dumps({"scope":"two version-pinned BEE_Birth and map helper functions, direct static imports only","versions":report},indent=2)+"\n",encoding="utf-8")
print("PASS 2/2 versions; data-map forwarded separately from built-in TDB type registration.")
print("OUTPUT",dest)
